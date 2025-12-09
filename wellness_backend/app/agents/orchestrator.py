from typing import Dict, Any, Optional
import json
import re

from langchain_core.messages import SystemMessage, HumanMessage

from app.llm import llm
from app.memory import get_memory
from app.db import save_history, get_last_interaction  # <- SQL integration

from .symptom_agent import SymptomAgent
from .diet_agent import DietAgent
from .fitness_agent import FitnessAgent
from .lifestyle_agent import LifestyleAgent
from .classifier import is_wellness_query


# ==============================
# Utility helpers
# ==============================


def _add_memory_message(memory, tag: str, content: str) -> None:
    """
    Store a tagged assistant message in LangChain memory.
    Example stored content: "[SymptomAgent] User has fever for 3 days."
    """
    if not content:
        return
    memory.chat_memory.add_ai_message(f"[{tag}] {content}")


def _safe_json_loads(raw: str) -> Dict[str, Any]:
    """
    Try to parse a JSON object from an LLM response.
    Falls back to extracting the first {...} block if needed.
    """
    raw = raw.strip()
    try:
        return json.loads(raw)
    except Exception:
        pass

    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {}


# ==============================
# LLM-based classifiers
# ==============================


def _is_follow_up_with_sql(
    user_message: str, user_id: str
) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    Use LLM to determine if the new message is a follow-up to the previous wellness issue.
    Uses SQL database to get the last interaction instead of LangChain memory.

    Returns:
        tuple: (is_follow_up: bool, previous_json: Optional[Dict])
    """
    # Get last interaction from SQL database
    last_interaction = get_last_interaction(user_id)

    if not last_interaction:
        print("[DEBUG] No previous interaction found in database")
        return False, None

    previous_message = last_interaction.get("user_message", "")
    previous_json = last_interaction.get("final_json", {})

    if not previous_message or not previous_json:
        print("[DEBUG] Incomplete previous interaction data")
        return False, None

    # Extract context from previous JSON
    symptom = previous_json.get("symptom", "")
    conclusion = previous_json.get("conclusion", "")
    diet_guidance = previous_json.get("diet_guidance", [])
    lifestyle_advice = previous_json.get("lifestyle_advice", [])
    physical_activity = previous_json.get("physical_activity_suggestions", [])

    # Build context of previous recommendations
    previous_recommendations = ""
    if diet_guidance:
        previous_recommendations += (
            f"\nDiet suggestions included: {', '.join(diet_guidance[:3])}"
        )
    if lifestyle_advice:
        previous_recommendations += (
            f"\nLifestyle suggestions included: {', '.join(lifestyle_advice[:3])}"
        )
    if physical_activity:
        previous_recommendations += (
            f"\nExercise suggestions included: {', '.join(physical_activity[:3])}"
        )

    system_prompt = """
You are a wellness conversation classifier. Analyze if the new user message is a FOLLOW-UP
to their previous wellness conversation or a COMPLETELY NEW health concern.

FOLLOW-UP indicators:
- User refers to advice, suggestions, or information already provided
- User asks "what about...", "can I also...", "any alternatives...", "what else..."
- User expresses preferences/dislikes about previous recommendations ("I don't like...", "I can't do...", "I have issue with...")
- User rejects or expresses inability to follow specific suggestions ("I can't do cycling", "I don't eat meat")
- User asks for clarification or more details about previous advice
- User provides CONSTRAINTS or LIMITATIONS related to following the previous advice
- User wants alternatives to what was suggested
- Context words: "also", "instead", "what if", "can I", "should I", "other", "different", "can't", "unable"

NEW QUERY indicators:
- A completely different symptom or health problem UNRELATED to the previous one
- User explicitly says "I have a new issue", "different problem", "another concern", "now I have..."
- The health topic has COMPLETELY changed with NO connection to previous advice

CRITICAL: 
- "I can't do X" where X was suggested in previous advice = FOLLOW-UP (asking for alternatives)
- "I have Y issue" mentioned as a REASON for not following advice = FOLLOW-UP (explaining limitation)
- "I have Y issue" as a NEW PRIMARY concern = NEW QUERY

EXAMPLES:
- Previous: stomach advice with cycling suggestion → "I can't do cycling, I have a leg issue" → FOLLOW-UP (rejecting cycling suggestion)
- Previous: headache advice → "Now I have stomach pain" → NEW QUERY (different symptom)
- Previous: diet advice with banana → "I don't like bananas" → FOLLOW-UP (rejecting food suggestion)

Respond with ONLY a JSON object:
{
  "is_follow_up": true/false,
  "confidence": "high/medium/low",
  "reason": "brief explanation"
}
"""

    human_prompt = f"""
Previous user message: "{previous_message}"
Previous symptom discussed: "{symptom}"
{previous_recommendations}

New user message: "{user_message}"

Is this new message a follow-up to the previous wellness conversation?
"""

    messages = [
        SystemMessage(content=system_prompt.strip()),
        HumanMessage(content=human_prompt.strip()),
    ]

    try:
        res = llm.invoke(messages).content.strip()
        print(f"[DEBUG] Follow-up detection response: {res}")
        parsed = _safe_json_loads(res)

        is_follow_up = parsed.get("is_follow_up", False)
        confidence = parsed.get("confidence", "low")
        reason = parsed.get("reason", "")

        print(
            f"[DEBUG] Parsed result - Follow-up: {is_follow_up}, Confidence: {confidence}, Reason: {reason}"
        )

        if is_follow_up:
            return True, previous_json
        else:
            return False, None

    except Exception as e:
        print(f"[DEBUG] Follow-up detection error: {e}")
        return False, None


def _classify_followup_section(
    user_message: str, previous_json: Dict[str, Any]
) -> Optional[str]:
    """
    Use LLM to choose which section of the final JSON should be updated.
    With comprehensive keyword fallback for robust classification.
    """
    system_prompt = """
You are a classifier for a wellness assistant.

A user has already received wellness advice with these sections:
- observations (symptom details)
- diet_guidance (food/nutrition)
- lifestyle_advice (habits/stress/sleep)
- physical_activity_suggestions (exercise)

Now the user sends a FOLLOW-UP asking about alternatives or different options.

Your task: Decide which ONE section to update based on the follow-up message.

CRITICAL EXAMPLES:
- "I don't like bananas" or "I can't eat leafy greens" → diet_guidance (food alternative)
- "I don't want to do yoga" or "I can't do cycling" → physical_activity_suggestions (exercise alternative)
- "I can't meditate" or "I don't like breathing exercises" → lifestyle_advice (habit alternative)
- "The pain is worse" or "I have a new symptom" → observations (symptom update)

Respond ONLY with JSON:
{
  "target_section": "diet_guidance" | "lifestyle_advice" | "physical_activity_suggestions" | "observations",
  "reason": "brief explanation"
}
"""

    prev_symptom = previous_json.get("symptom", "")
    prev_diet = previous_json.get("diet_guidance", [])
    prev_lifestyle = previous_json.get("lifestyle_advice", [])
    prev_physical = previous_json.get("physical_activity_suggestions", [])

    human_prompt = f"""
Previous symptom: {prev_symptom}

Previous diet suggestions: {', '.join(prev_diet[:2]) if prev_diet else 'None'}
Previous lifestyle suggestions: {', '.join(prev_lifestyle[:2]) if prev_lifestyle else 'None'}
Previous exercise suggestions: {', '.join(prev_physical[:2]) if prev_physical else 'None'}

User follow-up: "{user_message}"

Which section should be updated?
"""

    messages = [
        SystemMessage(content=system_prompt.strip()),
        HumanMessage(content=human_prompt.strip()),
    ]

    try:
        res = llm.invoke(messages).content.strip()
        parsed = _safe_json_loads(res)
        section = parsed.get("target_section")

        if section in {
            "observations",
            "diet_guidance",
            "lifestyle_advice",
            "physical_activity_suggestions",
        }:
            return section

        # LLM fallback: keyword matching
        res_lower = res.lower()
        if any(kw in res_lower for kw in ["diet", "food", "eat", "drink"]):
            return "diet_guidance"
        elif any(
            kw in res_lower for kw in ["exercise", "physical", "activity", "walk"]
        ):
            return "physical_activity_suggestions"
        elif any(kw in res_lower for kw in ["lifestyle", "sleep", "stress", "habit"]):
            return "lifestyle_advice"
        elif any(kw in res_lower for kw in ["symptom", "observation", "pain", "feel"]):
            return "observations"

    except Exception as e:
        print(f"[DEBUG] Classification error: {e}")

    # Final fallback: keyword matching in user message
    user_lower = user_message.lower()

    diet_keywords = [
        "food",
        "eat",
        "drink",
        "diet",
        "meal",
        "banana",
        "fruit",
        "vegetable",
        "milk",
        "water",
        "tea",
        "coffee",
        "juice",
        "dairy",
        "meat",
        "fish",
        "nut",
        "allerg",
    ]

    exercise_keywords = [
        "exercise",
        "walk",
        "workout",
        "gym",
        "run",
        "yoga",
        "cycling",
        "bike",
        "physical",
        "activity",
        "sport",
        "stretch",
        "fitness",
        "train",
    ]

    lifestyle_keywords = [
        "sleep",
        "stress",
        "routine",
        "habit",
        "relax",
        "meditation",
        "breathe",
        "breathing",
        "calm",
        "rest",
        "energy",
        "mood",
        "mental",
        "screen",
    ]

    symptom_keywords = [
        "pain",
        "hurt",
        "worse",
        "feel",
        "symptom",
        "ache",
        "discomfort",
        "severe",
        "improve",
        "better",
        "swell",
        "fever",
        "nausea",
    ]

    if any(kw in user_lower for kw in diet_keywords):
        return "diet_guidance"
    elif any(kw in user_lower for kw in exercise_keywords):
        return "physical_activity_suggestions"
    elif any(kw in user_lower for kw in lifestyle_keywords):
        return "lifestyle_advice"
    elif any(kw in user_lower for kw in symptom_keywords):
        return "observations"

    return None


# ==============================
# Final JSON builders
# ==============================

_BASE_SCHEMA = """
{
  "symptom": string,
  "observations": [string, ...],
  "diet_guidance": [string, ...],
  "lifestyle_advice": [string, ...],
  "physical_activity_suggestions": [string, ...],
  "conclusion": string
}
"""


def _build_final_json_new(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the final JSON for a NEW wellness query using all 4 agents' outputs.
    """
    user_input = state.get("user_input", "")
    symptom_summary = state.get("symptom_summary", "")
    diet_tip = state.get("diet_tip", "")
    fitness_tip = state.get("fitness_tip", "")
    lifestyle_tip = state.get("lifestyle_tip", "")

    system_prompt = f"""
You are a formatter for a digital wellness assistant.

You will receive:
- The user's original message.
- A one-line symptom summary.
- Short diet, fitness, and lifestyle suggestions from 3 agents.

Your task is ONLY to produce a VALID JSON object with this exact schema:
{_BASE_SCHEMA}

Rules:
- "symptom" must be ONE short line describing the issue.
- Each list must contain AT LEAST 5 short, clear points.
- Points should be plain sentences, no numbering or bullet characters.
- The conclusion is ONE short paragraph combining everything.
- Do NOT add explanations outside the JSON. Respond with JSON ONLY.
"""

    human_prompt = f"""
User message: {user_input}

Symptom summary: {symptom_summary}

Diet suggestions (raw): {diet_tip}

Fitness suggestions (raw): {fitness_tip}

Lifestyle suggestions (raw): {lifestyle_tip}
"""

    messages = [
        SystemMessage(content=system_prompt.strip()),
        HumanMessage(content=human_prompt.strip()),
    ]

    try:
        response = llm.invoke(messages)
        parsed = _safe_json_loads(response.content)
    except Exception:
        parsed = {}

    if not parsed:
        # Fallback
        symptom = symptom_summary or user_input or "User reported a wellness issue."
        fallback_point = "General wellness advice based on your symptom."
        parsed = {
            "symptom": symptom,
            "observations": [fallback_point] * 5,
            "diet_guidance": [fallback_point] * 5,
            "lifestyle_advice": [fallback_point] * 5,
            "physical_activity_suggestions": [fallback_point] * 5,
            "conclusion": (
                "This is a fallback response. The system could not format the "
                "detailed advice correctly, but your symptom has been noted."
            ),
        }

    return parsed


def _build_final_json_followup(
    previous_json: Dict[str, Any],
    state: Dict[str, Any],
    target_section: str,
) -> Dict[str, Any]:
    """
    Build the final JSON for a FOLLOW-UP query.

    Rules:
    - symptom is copied EXACTLY from previous_json.
    - ALL sections except target_section are copied EXACTLY.
    - ONLY target_section is regenerated.
    - conclusion is always regenerated to align with the updated section.
    """
    user_input = state.get("user_input", "")

    prev_symptom = previous_json.get("symptom", "")
    prev_observations = previous_json.get("observations", [])
    prev_diet = previous_json.get("diet_guidance", [])
    prev_lifestyle = previous_json.get("lifestyle_advice", [])
    prev_physical = previous_json.get("physical_activity_suggestions", [])
    prev_conclusion = previous_json.get("conclusion", "")

    # New raw info from agents depending on target section
    if target_section == "diet_guidance":
        new_raw = state.get("diet_tip", "")
    elif target_section == "lifestyle_advice":
        new_raw = state.get("lifestyle_tip", "")
    elif target_section == "physical_activity_suggestions":
        new_raw = state.get("fitness_tip", "")
    elif target_section == "observations":
        new_raw = state.get("symptom_summary", "")
    else:
        # Unknown target → just return previous JSON untouched
        return previous_json

    previous_json_str = json.dumps(previous_json, ensure_ascii=False)

    system_prompt = f"""
You are a formatter for a digital wellness assistant in FOLLOW-UP mode.

The user has already received a final JSON for a wellness issue.

You will receive:
- The user's follow-up message.
- The previous final JSON (previous_json).
- The name of the target section to update.
- New raw information from the relevant agent.

Your task is to produce a NEW JSON with this exact schema:
{_BASE_SCHEMA}

CRITICAL RULES:
- You MUST copy these fields EXACTLY from previous_json, WITHOUT changing any text
  or order:
    * "symptom"
    * Every list field EXCEPT the target_section.
- You are allowed to MODIFY ONLY:
    * The list specified by target_section.
    * "conclusion" (rewrite so it aligns with the updated section and overall context).
- The updated target_section must have at least 5 short, clear points.
- All other lists must remain exactly as in previous_json (same text, same order).
- The new "conclusion" must be one short paragraph that:
    * Acknowledges the user's constraint or preference mentioned in the follow-up
    * Introduces the alternative suggestions provided
    * Maintains the context of the original symptom
    * Example: "As you mentioned you're unable to do cycling due to a leg issue, here are alternative exercises..."
- Do NOT mention that this is a follow-up inside the JSON.
- Do NOT add any explanation outside the JSON. Respond with JSON ONLY.
"""

    human_prompt = f"""
User follow-up message: {user_input}

target_section to update: {target_section}

previous_json:
{previous_json_str}

New raw info for the target section (from agent):
{new_raw}

Previous conclusion:
{prev_conclusion}
"""

    messages = [
        SystemMessage(content=system_prompt.strip()),
        HumanMessage(content=human_prompt.strip()),
    ]

    try:
        response = llm.invoke(messages)
        parsed = _safe_json_loads(response.content)
    except Exception:
        parsed = {}

    if not parsed:
        # Fallback: return previous JSON if we can't safely build new one
        return previous_json

    return parsed


def _handle_non_wellness_query(user_input: str) -> Dict[str, Any]:
    """
    For NON-wellness messages, redirect user to wellness-related topics.
    Return a structured response that politely declines and guides them.
    """
    system_prompt = """
You are a wellness assistant that ONLY handles health and wellness related queries.

The user's message is NOT related to wellness, health, lifestyle, or fitness.

Your task: Provide a POLITE and HELPFUL response that:
1. Clearly states this system is for wellness guidance only
2. Examples of wellness topics the system CAN help with
3. Encourages them to ask health/wellness related questions
4. Keep response concise (2-3 sentences max)

Examples of wellness topics:
- Symptoms and health concerns (headache, stomach pain, fatigue, etc.)
- Diet and nutrition advice
- Exercise and fitness recommendations
- Stress management and lifestyle changes
- Sleep quality and mental health

Do NOT attempt to answer their non-wellness question.
Focus on redirecting them politely to wellness topics.
"""

    human_prompt = f"""
User message: "{user_input}"

Provide a polite response redirecting them to wellness-related questions.
"""

    messages = [
        SystemMessage(content=system_prompt.strip()),
        HumanMessage(content=human_prompt.strip()),
    ]

    try:
        response = llm.invoke(messages)
        answer = response.content.strip()
    except Exception:
        answer = (
            "This system provides wellness guidance for health concerns, diet advice, "
            "fitness recommendations, and lifestyle improvements. Please ask any questions "
            "related to your health and wellness."
        )

    return {
        "symptom": "",
        "observations": [],
        "diet_guidance": [],
        "lifestyle_advice": [],
        "physical_activity_suggestions": [],
        "conclusion": answer,
    }


# ==============================
# Main entry point
# ==============================


def run_wellness_flow(user_id: str, user_input: str) -> Dict[str, Any]:
    """
    Entry point used by the FastAPI endpoint.

    Flow:
    1. Check if the message is wellness-related.
    2. If NOT wellness:
       - Answer normally, wrap in JSON (only conclusion used).
    3. If wellness:
       - Detect if this is a follow-up to previous advice.
       - If FOLLOW-UP:
           * Load last FinalAdviceJSON from history.
           * If none: treat as NEW.
           * If found:
               - Use LLM to choose which section to update.
               - Re-run only the corresponding agent:
                   observations -> SymptomAgent
                   diet_guidance -> DietAgent
                   lifestyle_advice -> LifestyleAgent
                   physical_activity_suggestions -> FitnessAgent
               - Build new JSON by copying everything except that section,
                 and regenerate conclusion.
       - If NEW:
           * Run all 4 agents with manual handoff.
           * Build full combined JSON.
       - Store full final JSON in memory tagged as [FinalAdviceJSON].
       - Also persist each interaction in SQL via save_history.
    """
    memory = get_memory(user_id)

    # Store raw user message
    memory.chat_memory.add_user_message(user_input)

    # 1) Non-wellness handling
    if not is_wellness_query(user_input):
        result = _handle_non_wellness_query(user_input)
        _add_memory_message(memory, "NonWellness", result["conclusion"])

        # Save non-wellness interaction as well (no target_section)
        save_history(
            user_id=user_id,
            user_message=user_input,
            final_json=result,
            is_follow_up=False,
            target_section=None,
        )
        return result

    # 2) Detect follow-up using SQL database and LLM
    print(f"[DEBUG] User: {user_id}")
    print(f"[DEBUG] Message: {user_input}")

    follow_up, previous_json = _is_follow_up_with_sql(user_input, user_id)

    print(f"[DEBUG] Follow-up detected: {follow_up}")
    if previous_json:
        print(f"[DEBUG] Previous symptom: {previous_json.get('symptom', 'N/A')}")

    # Instantiate agents
    agents = {
        "SymptomAgent": SymptomAgent(llm),
        "DietAgent": DietAgent(llm),
        "FitnessAgent": FitnessAgent(llm),
        "LifestyleAgent": LifestyleAgent(llm),
    }

    # --------------------------
    # FOLLOW-UP FLOW
    # --------------------------
    if follow_up:
        # previous_json already retrieved from SQL in _is_follow_up_with_sql
        if previous_json is not None:
            target_section = _classify_followup_section(user_input, previous_json)
            print(f"[DEBUG] Target section for follow-up: {target_section}")

            if target_section in {
                "observations",
                "diet_guidance",
                "lifestyle_advice",
                "physical_activity_suggestions",
            }:
                # Prepare state with context
                state: Dict[str, Any] = {"user_input": user_input}
                state["symptom_summary"] = previous_json.get("symptom", "")

                # Re-run only the relevant agent
                if target_section == "diet_guidance":
                    agent = agents["DietAgent"]
                    result = agent.run(state)
                    state = result["state"]
                    _add_memory_message(memory, "DietAgent", state.get("diet_tip", ""))

                elif target_section == "lifestyle_advice":
                    agent = agents["LifestyleAgent"]
                    result = agent.run(state)
                    state = result["state"]
                    _add_memory_message(
                        memory, "LifestyleAgent", state.get("lifestyle_tip", "")
                    )

                elif target_section == "physical_activity_suggestions":
                    agent = agents["FitnessAgent"]
                    result = agent.run(state)
                    state = result["state"]
                    _add_memory_message(
                        memory, "FitnessAgent", state.get("fitness_tip", "")
                    )

                elif target_section == "observations":
                    agent = agents["SymptomAgent"]
                    result = agent.run(state)
                    state = result["state"]
                    _add_memory_message(
                        memory, "SymptomAgent", state.get("symptom_summary", "")
                    )

                # Build updated JSON
                final_json = _build_final_json_followup(
                    previous_json=previous_json,
                    state=state,
                    target_section=target_section,
                )

                # Store full JSON in memory
                full_json_str = json.dumps(final_json, ensure_ascii=False)
                _add_memory_message(memory, "FinalAdviceJSON", full_json_str)

                # Persist follow-up interaction in SQL
                save_history(
                    user_id=user_id,
                    user_message=user_input,
                    final_json=final_json,
                    is_follow_up=True,
                    target_section=target_section,
                )

                print(
                    f"[DEBUG] Follow-up processed successfully for section: {target_section}"
                )
                return final_json
            else:
                print(
                    f"[DEBUG] Invalid target section: {target_section}, treating as new query"
                )
        else:
            print("[DEBUG] No previous JSON found, treating as new query")
        # If no previous_json or classification fails → fall through to NEW flow

    # --------------------------
    # NEW WELLNESS FLOW
    # --------------------------
    print("[DEBUG] Processing as NEW wellness query")
    state: Dict[str, Any] = {"user_input": user_input}
    state["symptom_summary"] = ""
    current_agent_name: Optional[str] = "SymptomAgent"

    while current_agent_name is not None:
        agent = agents[current_agent_name]
        result = agent.run(state)
        state = result["state"]
        next_agent = result.get("next")

        # Per-agent memory logging
        if current_agent_name == "SymptomAgent":
            _add_memory_message(
                memory, "SymptomAgent", state.get("symptom_summary", "")
            )
        elif current_agent_name == "DietAgent":
            _add_memory_message(memory, "DietAgent", state.get("diet_tip", ""))
        elif current_agent_name == "FitnessAgent":
            _add_memory_message(memory, "FitnessAgent", state.get("fitness_tip", ""))
        elif current_agent_name == "LifestyleAgent":
            _add_memory_message(
                memory, "LifestyleAgent", state.get("lifestyle_tip", "")
            )

        current_agent_name = next_agent

    # Build final JSON for new case
    final_json = _build_final_json_new(state)

    # Store full final JSON in memory as a single line
    full_json_str = json.dumps(final_json, ensure_ascii=False)
    _add_memory_message(memory, "FinalAdviceJSON", full_json_str)

    # Persist NEW interaction in SQL
    save_history(
        user_id=user_id,
        user_message=user_input,
        final_json=final_json,
        is_follow_up=False,
        target_section=None,
    )

    return final_json
