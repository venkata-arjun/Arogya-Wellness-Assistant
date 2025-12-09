# Arogya Wellness Assistant - Frontend

A modern React-based frontend application for the Arogya Wellness Assistant, an AI-powered multi-agent wellness chatbot that provides personalized health guidance across diet, lifestyle, fitness, and symptom analysis.

## 🎯 Features

- **Interactive Chat Interface**: Real-time conversation with the wellness assistant
- **Smart Symptom Analysis**: AI-powered classification and analysis of health symptoms
- **Multi-Agent Guidance**:
  - Diet recommendations
  - Lifestyle advice
  - Fitness suggestions
  - Symptom observations
- **Dark Mode Support**: Toggle between light and dark themes
- **Persistent Chat History**: Local storage of conversation history
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Message Copy Function**: Easy copy-to-clipboard for wellness advice
- **Home Screen**: Welcome screen with app introduction
- **User Sessions**: Per-browser user tracking for maintaining context

## 🚀 Quick Start

### Prerequisites

- Node.js 16+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd wellness_frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The app will open at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

The production build is generated in the `dist/` folder.

### Preview Production Build

```bash
npm run preview
```

## 📁 Project Structure

```
wellness_frontend/
├── src/
│   ├── api/
│   │   ├── client.js           # API client configuration
│   │   └── wellness.js         # Wellness API endpoints
│   ├── assets/
│   │   ├── logo.png            # Light mode logo
│   │   └── black-logo.png      # Dark mode logo
│   ├── App.jsx                 # Main application component
│   ├── App.css                 # Styling with Tailwind
│   ├── main.jsx                # React entry point
│   └── index.html              # HTML template
├── package.json
├── vite.config.js
├── eslint.config.js
└── README.md
```

## 🔧 Key Technologies

- **React 19.2**: Modern UI library
- **Vite 7.2**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework (via class names)
- **Lucide React**: Beautiful icon library
  - Send, Bot, Loader2, Copy, Check, Sun, Moon, ArrowRightCircle icons

## 📡 API Integration

The frontend communicates with the backend via REST API:

### Endpoints Used

**POST `/api/wellness`**

- Send a wellness-related message
- Request body: `{ user_id: string, message: string }`
- Response: `{ user_id: string, final_output: {...} }`

**GET `/api/history/{user_id}`**

- Retrieve conversation history for a user
- Response: Array of history items with timestamps and agent responses

### Response Format

Each wellness response includes:

```json
{
  "symptom": "string",
  "observations": ["string", ...],
  "diet_guidance": ["string", ...],
  "lifestyle_advice": ["string", ...],
  "physical_activity_suggestions": ["string", ...],
  "conclusion": "string"
}
```

## 🎨 UI Components

### Home Screen

- Welcome banner with Arogya logo
- Introduction text
- "Start Chat" button to enter the application

### Chat Interface

- **Header**: App title with dark mode toggle
- **Chat Area**: Scrollable message history with timestamps
- **Message Bubbles**:
  - User messages (blue, right-aligned)
  - Bot messages (gray, left-aligned with avatar)
  - Copy button for bot responses
- **Input Footer**: Message textarea and send button
- **Status Indicators**: Loading spinner while waiting for response

### Dark Mode

- Automatic theme switching with persistent state
- Adapted colors for all components
- Light and dark logos for branding

## 💾 Local Storage

The app uses browser's LocalStorage to persist:

- **wellness_user_id**: Unique user identifier per browser
- **wellness_chat_history**: Full conversation history

## 🔄 Message Flow

1. User types a wellness-related question
2. Frontend sends message to backend API
3. Backend processes through multi-agent system:
   - SymptomAgent: Analyzes the symptom
   - DietAgent: Provides dietary guidance
   - FitnessAgent: Suggests physical activities
   - LifestyleAgent: Recommends lifestyle changes
4. Backend returns structured JSON response
5. Frontend formats and displays the response with:
   - Bold section headers
   - Bulleted advice items
   - Comprehensive conclusion

## ✨ User Experience Features

### Formatting

- **Bold headers** for each advice section
- **Bullet points** for easy readability
- **Automatic text wrapping** for long content
- **Timestamps** for each message

### Copy Functionality

- Click copy icon on any bot response
- Text automatically formatted for clipboard
- Visual feedback (checkmark for 1.2 seconds)

### Error Handling

- Connection error messages with user-friendly text
- Graceful fallback for failed requests
- Retry capability by sending new message

## 🛠️ Development Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

## 🌐 Environment Configuration

Update the API base URL in `src/api/client.js` if the backend runs on a different host/port:

```javascript
const API_BASE_URL = "http://localhost:8000";
```

## 📱 Responsive Breakpoints

The application is optimized for:

- **Mobile**: < 640px (sm)
- **Tablet**: 640px - 1024px (md)
- **Desktop**: > 1024px (lg)

Responsive adjustments:

- Smaller padding/margins on mobile
- Adjusted font sizes for readability
- Touch-friendly button sizes
- Optimized chat bubble widths

## 🔐 Security Notes

- User IDs are generated randomly and stored locally
- No sensitive data stored in LocalStorage
- CORS configured to accept requests from frontend origin
- All API calls use POST/GET over HTTP (upgrade to HTTPS in production)

## 🐛 Troubleshooting

### "Unable to connect to API"

- Ensure backend server is running on `localhost:8000`
- Check CORS settings in backend
- Verify network connectivity

### Chat history not persisting

- Check browser's LocalStorage is enabled
- Clear browser cache if experiencing issues
- Try incognito mode to test

### Dark mode not working

- Verify Tailwind CSS is properly configured
- Check browser DevTools for CSS class application
- Clear browser cache

## 📚 Learn More

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vite.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com)
- [Lucide React Icons](https://lucide.dev)

## 📄 License

Part of the Arogya Wellness Assistant project.

## 🤝 Support

For issues, questions, or contributions, please refer to the main project documentation.
