# 🌙 Starlit Stories - AI Story Teller

A child-safe storytelling web application powered by LangGraph that generates age-appropriate stories for children ages 5–10, complete with narrative arcs and moral lessons.

## ✨ Features

### Beautiful Web Interface
- 🌌 **Fading Nebula Glow Theme**: Animated starfield background with purple-gold nebula
- 💫 **3D Flip Cards**: Right-click stories to reveal moral summaries
- 🎭 **Smooth Animations**: Glowing text effects and loading indicators
- 📱 **Responsive Design**: Works beautifully on desktop and mobile
- 🔄 **Conversation Memory**: Maintains context to modify existing stories

### Intelligent Story Generation
- 🛡️ **Child-Safe Content**: Strict validation for ages 5-10
- 🎭 **Smart Routing**: Understands greetings, farewells, story requests, and modifications
- 🔄 **Story Modifications**: "Make the hero braver", "Add more animals", etc.
- 📖 **Classic Story Retrieval**: Can tell well-known fairy tales
- 🎨 **Flexible Lengths**: Short, medium, or long stories
- 🧠 **Context-Aware**: Remembers conversation history for natural interactions

## 🚀 Quick Start

### 1. Setup (First Time Only)

```powershell
# Run the setup script
.\setup.bat
```

This will:
- Install Python dependencies (FastAPI, LangGraph, etc.)
- Install frontend dependencies (React, Vite, etc.)
- Create your `.env` file
- Prompt you to add your Gemini API key

### 2. Get Your API Key

Visit [Google AI Studio](https://makersuite.google.com/app/apikey) to get a free Gemini API key.

Add it to your `.env` file:
```bash
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Start the Application

```powershell
# Start both backend and frontend
.\start-all.bat
```

This opens:
- Backend server on http://localhost:8000
- Frontend app on http://localhost:5173

Your browser should automatically open to the app!

### 4. Create Stories!

Try these requests:
- "Tell me a story about a brave little mouse"
- "I want to hear about a friendly dragon who loves to bake"
- "Story about two octopuses becoming friends"

**Right-click on the story card** to flip it and reveal the moral! ✨

### 5. Modify Stories

After generating a story, you can request changes:
- "Make the hero braver"
- "Add more animals to the forest"
- "Change the ending to be happier"
- "Remove the villain from the story"

## 🎮 Usage Examples

### Natural Conversation Flow

```
You: Hello!
Agent: Hi there! I'm your friendly story teller. What kind of story would you like to hear?

You: Tell me about two octopuses who become friends
Agent: [Generates story about Inky and Ollie building an ocean garden]

You: Make them find a treasure instead
Agent: [Modifies the story to include a treasure hunt]

You: Thank you! Goodnight!
Agent: Sweet dreams! Come back anytime for more stories!
```

### Story Features

- **Right-click** the story card (or **long-press** on mobile) to flip and see the moral
- Stories are displayed with beautiful typography and glow effects
- Loading animations show while the AI is thinking
- All responses maintain conversation context

## 🏗️ Architecture

### Backend (FastAPI + LangGraph)

Six specialized AI nodes work together:

1. **MainAgent** - Routes requests (new story, modification, greeting, farewell)
2. **StoryGenerator** - Creates original stories or modifies existing ones
3. **StoryChecker** - Validates appropriateness and quality
4. **MoralSummarizer** - Extracts moral lessons
5. **StoryRetriever** - Retrieves canonical classic stories
6. **Formatter** - Formats output for beautiful display

### Frontend (React + TypeScript + Vite)

- Modern React with TypeScript
- Tailwind CSS for styling
- Axios for API communication
- 3D CSS transforms for flip cards
- Custom starfield animations

## 📁 Project Structure

```
starlit-stories/
├── src/
│   ├── api/
│   │   └── server.py           # FastAPI backend
│   └── react_agent/
│       ├── graph.py            # LangGraph workflow
│       ├── tools/
│       │   └── tools.py        # Node implementations
│       ├── prompts/            # AI prompts (editable!)
│       │   ├── main_agent_prompt.txt
│       │   ├── story_generator_prompt.txt
│       │   ├── story_checker_prompt.txt
│       │   └── ...
│       └── services/
│           └── llm_client.py   # LLM provider
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main React component
│   │   ├── components/
│   │   │   └── FlipCard.tsx    # 3D flip card
│   │   ├── api/
│   │   │   └── generateStory.ts # API client
│   │   └── index.css           # Starfield animations
│   ├── index.html
│   └── package.json
├── .env                        # Your API keys (don't commit!)
├── .env.example               # Template
├── pyproject.toml             # Python dependencies
├── start-all.bat              # Start both servers
├── start-backend.bat          # Start backend only
├── start-frontend.bat         # Start frontend only
└── restart-backend.bat        # Restart backend
```

## ⚙️ Configuration

Edit `.env` to customize:

```bash
# Required
GEMINI_API_KEY=your_key_here

# Optional settings
MAX_STORY_ITERATIONS=3          # Story refinement loops
DEFAULT_STORY_LENGTH=medium     # short, medium, or long
ENABLE_SAFETY_CHECKS=true      # Content safety
STRICT_MODE=true               # Extra strict filtering
```

## 🎨 Customization

### Modify AI Prompts

All AI prompts are in `src/react_agent/prompts/` as editable text files:
- `main_agent_prompt.txt` - Routing and classification logic
- `story_generator_prompt.txt` - Story creation instructions
- `story_checker_prompt.txt` - Safety validation rules
- `moral_summarizer_prompt.txt` - Moral extraction
- `formatter_prompt.txt` - Output formatting

Edit these to change how the AI behaves!

### Customize the Theme

Edit `frontend/src/index.css` to change:
- Color scheme (currently purple/gold)
- Animation speeds
- Glow effects
- Starfield density

## 🛡️ Safety Features

- **Age-Appropriate Content**: All stories validated for ages 5-10
- **Multi-Layer Filtering**: Both keyword and AI-based safety checks
- **Gentle Refusals**: Kind explanations when content isn't appropriate
- **No Inappropriate Themes**: Blocks violence, adult themes, scary content, etc.

## 🔧 Troubleshooting

### Backend won't start
- Check that port 8000 is not in use
- Verify your `.env` has a valid `GEMINI_API_KEY`
- Run `poetry install` to ensure dependencies are installed

### Frontend won't start
- Check that port 5173 is not in use
- Run `cd frontend && npm install` to install dependencies
- Try `npm run dev` manually in the frontend folder

### Stories aren't generating
- Check the backend terminal for errors
- Verify your Gemini API key is valid
- Check your internet connection

### Modifications not working
- Make sure you're using the same browser session (cookies maintain thread_id)
- Check backend logs to see if it's detecting conversation history
- Try refreshing the page to start a new conversation

## 🛑 Stopping the Servers

**Option 1**: Press `Ctrl + C` in each terminal window

**Option 2**: Close the terminal windows

**Option 3**: Run the cleanup script (coming soon)

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) - AI workflow orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend framework
- [Vite](https://vitejs.dev/) - Build tool
- [Google Gemini](https://ai.google.dev/) - AI model

---

## 💡 Tips

- **Right-click stories** to see the moral
- **Use natural language** - the AI understands casual conversation
- **Modify stories** after generating them
- **Try different themes** - animals, space, underwater, magic, etc.
- **Say goodbye properly** - "Goodnight" or "Thank you" for a nice farewell

**Have fun creating magical stories!** 🌟
