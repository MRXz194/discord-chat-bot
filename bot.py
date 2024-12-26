# Author name: MRX
# Date and time: 12/26/2024 09:14 AM
# Day: Thursday
# Description : chatbot for discord using google gemini api
# github: https://github.com/MRXz194   Discord: kz5198
import os
import json
import discord
from discord.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv


BOT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BOT_DIR, 'settings.json')

load_dotenv()


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# styles
AVAILABLE_STYLES = {
    "professional": "like a name ans pro and formal",
    "friendly": "chill guy",
    "concise": "ans precise",
    "detailed": "ans more detailed",
    "simple": "short and simple ez understand",
    "technical": "tech topic",
    "creative": "use for creative prob",
    "teaching": "explain step by step"
}

def get_style_prompt(style):
    """Get the appropriate prompt modification based on style"""
    style_prompts = {
        "professional": """Maintain a professional tone:
- Use formal language and proper terminology
- Structure responses clearly and logically
- Stay objective and business-focused
- Avoid casual language and emojis""",

        "friendly": """Be warm and approachable:
- Use casual, conversational language
- Include appropriate emojis occasionally 😊
- Be encouraging and supportive
- Keep the tone light and engaging""",

        "concise": """Be direct and precise:
- Get straight to the point
- Focus on essential information
- Use clear, short sentences
- Avoid unnecessary elaboration""",

        "detailed": """Provide comprehensive information:
- Give thorough explanations
- Include relevant examples
- Cover multiple aspects of the topic
- Provide context and background""",

        "simple": """Keep it easy to understand:
- Use simple, everyday language
- Avoid technical jargon
- Explain concepts clearly
- Use relatable examples""",

        "technical": """Focus on technical accuracy:
- Use proper technical terminology
- Include technical specifications
- Provide detailed technical explanations
- Reference technical standards when relevant""",

        "creative": """Be imaginative and engaging:
- Use creative analogies
- Include interesting examples
- Make explanations engaging
- Think outside the box""",

        "teaching": """Adopt an educational approach:
- Break down concepts step by step
- Provide clear examples
- Check understanding
- Build on previous knowledge"""
    }
    
    return style_prompts.get(style, style_prompts["friendly"])

def get_style_config(style):
    """Get generation config modifications based on style"""
    style_configs = {
        "professional": {"temperature": 0.3, "top_p": 0.85},  # More consistent, formal responses
        "friendly": {"temperature": 0.7, "top_p": 0.95},      # More varied, casual responses
        "concise": {"temperature": 0.2, "top_p": 0.8},        # Very focused responses
        "detailed": {"temperature": 0.4, "top_p": 0.9},       # Balanced detail and coherence
        "simple": {"temperature": 0.3, "top_p": 0.85},        # Clear, straightforward responses
        "technical": {"temperature": 0.2, "top_p": 0.8},      # Precise technical responses
        "creative": {"temperature": 0.8, "top_p": 0.95},      # More creative variation
        "teaching": {"temperature": 0.4, "top_p": 0.9}        # Balanced teaching responses
    }
    return style_configs.get(style, style_configs["friendly"])

# Default 
DEFAULT_SETTINGS = {
    "temperature": 0.3,  # Lower temperature for more consistent responses
    "max_tokens": 2000,  # Increased token limit for more detailed responses
    "language": "English",
    "style": "friendly"
}

# User storage
user_settings = {}

def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_settings():
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(user_settings, f)

# Load setting
user_settings = load_settings()

def get_user_settings(user_id):
    if str(user_id) not in user_settings:
        user_settings[str(user_id)] = DEFAULT_SETTINGS.copy()
        save_settings()
    return user_settings[str(user_id)]

# Configure Gemini 
def get_generation_config(user_id):
    settings = get_user_settings(user_id)
    style_config = get_style_config(settings["style"])
    
    return genai.types.GenerationConfig(
        temperature=style_config["temperature"],
        top_p=style_config["top_p"],
        top_k=40,
        max_output_tokens=settings["max_tokens"],
        candidate_count=1,
    )

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

# Image onfig
SUPPORTED_IMAGE_TYPES = {
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/gif': '.gif',
    'image/webp': '.webp'
}

MAX_IMAGE_SIZE = 4 * 1024 * 1024  # 4MB limit

def process_image_response(response_text, is_casual=False):
    """Process image analysis response based on style"""
    if is_casual:
        return f"👀 Here's what I see: {response_text}"
    return f"Image Analysis:\n{response_text}"

# Conversation memory 
class Conversation:
    def __init__(self):
        self.history = []
        self.last_topic = None

    def add_message(self, role, content):
        # Map roles 
        mapped_role = "user" if role == "user" else "model"
        
        message = {
            "role": mapped_role,
            "parts": [content]
        }
        
        self.history.append(message)
        
        # Store last topic 
        if role == "user" and not any(word in content.lower() for word in [
            "more", "explain", "elaborate", "details", "examples", "continue"
        ]):
            self.last_topic = content

    def get_messages(self):
        return self.history

    def get_last_topic(self):
        
        return self.last_topic # Return the last topic

    def clear(self):
        self.history = []
        self.last_topic = None

def is_casual_chat(text): 
    """Check if the message is a casual greeting or chat"""
    casual_patterns = [
        'hi', 'hello', 'hey', 'sup', 'yo', 'hiya', 'good morning', 
        'good afternoon', 'good evening', 'howdy', 'what\'s up', 
        'how are you', 'how\'s it going', 'whats up', 'greetings'
    ]
    return text.lower().strip() in casual_patterns

def get_enhanced_prompt(question, style_prompt, conv): # Add more context to enchance the prompt
    """Generate an enhanced prompt with better context and instructions"""
    
    # question type
    code_keywords = [
        "write code", "generate code", "create a program", "write a function",
        "write a class", "implement", "code example", "write script",
        "programming", "function to", "class that", "code for", "write", "code"
    ]
    
    explanation_keywords = [
        "explain", "how does", "what is", "why does", "describe",
        "tell me about", "what are", "define", "elaborate"
    ]
    
    comparison_keywords = [
        "difference between", "compare", "versus", "vs",
        "better than", "pros and cons", "advantages"
    ]
    
    debug_keywords = [
        "debug", "fix", "error", "not working", "issue",
        "problem", "bug", "wrong", "fail", "help with"
    ]

    # Determine type
    is_code_request = any(keyword in question.lower() for keyword in code_keywords)
    is_explanation = any(keyword in question.lower() for keyword in explanation_keywords)
    is_comparison = any(keyword in question.lower() for keyword in comparison_keywords)
    is_debug = any(keyword in question.lower() for keyword in debug_keywords)
    
    
    context = ""
    last_topic = conv.get_last_topic()# Get the last topic
    
    if last_topic and len(conv.history) > 0:
        context = "\nPrevious topic: " + last_topic
        
        last_exchanges = conv.history[-4:] if len(conv.history) >= 4 else conv.history
        context += "\nRecent conversation:\n"
        for msg in last_exchanges:
            context += f"{msg['role']}: {msg['parts'][0]}\n"

    
    if is_code_request:
        prompt = f"""Generate code based on this request: {question}

Requirements:
1. Write clean, efficient code
2. Include necessary imports
3. Add brief comments
4. Use proper formatting

Format the response as:
```python
# Your code here
```

Keep the code concise and focused."""
        return prompt

    elif is_explanation:
        prompt = f"""Provide a clear and comprehensive explanation.

Question: {question}

Guidelines:
- Start with a concise overview
- Break down complex concepts
- Use analogies when helpful
- Provide relevant examples
- Include practical applications
- Address common misconceptions

Previous context:{context}
{style_prompt}"""

    elif is_comparison:
        prompt = f"""Compare and contrast the subjects thoroughly.

Question: {question}

Structure:
1. Brief overview of both subjects
2. Key differences
3. Key similarities
4. Pros and cons of each
5. Common use cases
6. Recommendation if applicable

Previous context:{context}
{style_prompt}"""

    elif is_debug:
        prompt = f"""Help debug and fix the issue.

Problem: {question}

Approach:
1. Identify potential issues
2. Suggest solutions
3. Explain why the problem occurs
4. Provide corrected code if applicable
5. Suggest preventive measures

Previous context:{context}
{style_prompt}"""

    else:
        # promt for general question
        prompt = f"""Provide a helpful and informative response.

Question: {question}

Guidelines:
- Be accurate and up-to-date
- Include relevant examples
- Explain any technical terms
- Provide practical applications
- Consider different perspectives

Previous context:{context}
{style_prompt}"""

    # Add general response 
    prompt += """

Response Guidelines:
- Be clear and concise
- Use markdown formatting for better readability
- Include relevant examples
- Cite sources if applicable
- Maintain the specified conversation style
- If uncertain, acknowledge limitations
"""

    return prompt

def get_response_text(response):
    """Safely extract text from Gemini response"""
    try:
        # For simple text 
        if hasattr(response, 'text'):
            return response.text.strip()
            
        # For multi 
        if hasattr(response, 'parts'):
            parts_text = []
            for part in response.parts:
                if hasattr(part, 'text'):
                    parts_text.append(part.text.strip())
            if parts_text:
                return ' '.join(parts_text)
                
        # For candidate
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate.content, 'parts'):
                parts_text = []
                for part in candidate.content.parts:
                    if hasattr(part, 'text'):
                        parts_text.append(part.text.strip())
                if parts_text:
                    return ' '.join(parts_text)
                    
        return None
    except Exception as e:
        print(f"Error extracting response text: {str(e)}")
        return None

def split_into_messages(text, max_length=1900):
    """Split text into Discord-friendly chunks"""
    messages = []
    current_message = ""
    
    # Split code blocks and text
    parts = text.split("```")
    for i, part in enumerate(parts):
        is_code_block = i % 2 == 1
        
        if is_code_block:
            #  code blocks
            if len(current_message) + len(part) + 6 > max_length:  # 6 for the ``` markers
                if current_message:
                    messages.append(current_message)
                    current_message = ""
                
                # Split large code blocks
                code_chunks = [part[i:i+max_length-8] for i in range(0, len(part), max_length-8)]
                for chunk in code_chunks[:-1]:
                    messages.append(f"```{chunk}```")
                current_message = f"```{code_chunks[-1]}```" if code_chunks else ""
            else:
                current_message += f"```{part}```"
        else:
            # regular text
            sentences = part.split('. ')
            for sentence in sentences:
                if sentence:
                    if len(current_message) + len(sentence) + 2 > max_length:
                        messages.append(current_message.strip())
                        current_message = sentence + '. '
                    else:
                        current_message += sentence + '. '
    
    if current_message:
        messages.append(current_message.strip())
    
    return messages

# Store conversation
conversations = {}

def get_conversation(user_id, channel_id): # Get conversation
    key = f"{user_id}_{channel_id}"# Key
    if key not in conversations:
        conversations[key] = Conversation()
    return conversations[key]

# Message history prevent dup :v (hmmm maybe bug i dont know)
message_history = {}

def get_response_title(question, style):
    """Get appropriate title for response based on question type and style"""
    style_icons = {
        "professional": "👔",
        "friendly": "😊",
        "concise": "📝",
        "detailed": "📚",
        "simple": "💡",
        "technical": "⚙️",
        "creative": "🎨",
        "teaching": "📖"
    }
    
    #  icon
    style_icon = style_icons.get(style, "🤖")
    
    # Check casual chat
    if is_casual_chat(question):
        return "👋 Chat"
        
    # Check these qíe
    is_followup = any(word in question.lower() for word in [
        "more", "explain more", "tell me more", "elaborate", 
        "details", "examples", "continue", "what else"
    ]) or question.lower().strip() in ["more"]
    
    if is_followup:
        return f"{style_icon} Detailed Response"
        
    return f"{style_icon} Quick Overview"

@bot.event 
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="Type !help"))

@bot.command(name='help') # Help command
async def help(ctx):
    """Show help message"""
    embed = discord.Embed(
        title="🤖 Gemini Bot Help",
        description="Here's what I can do for you!",
        color=discord.Color.blue()
    )

    # Main 
    main_commands = (
        "**🗣️ Chat Commands**\n"
        "`!ask <question>` - Ask me anything! I can help with:\n"
        "• General questions and explanations\n"
        "• Code-related questions and debugging\n"
        "• Image analysis (attach an image)\n"
        "• Follow-up questions (just say `!ask more`)\n"
    )
    embed.add_field(name="Main Features", value=main_commands, inline=False)

    # Style 
    style_commands = (
        "**🎨 Style Settings**\n"
        "`!styles` - View available chat styles\n"
        "`!ask set_setting style <style>` - Change my chat style\n"
        "`!settings` - View your current settings\n"
    )
    embed.add_field(name="Personalization", value=style_commands, inline=False)

    # Utility 
    utility_commands = (
        "**🛠️ Utility Commands**\n"
        "`!ask clear` - Clear chat history\n"
        "`!ask reset` - Reset all settings\n"
        "`!ask reset_conversation` - Reset only the conversation\n"
    )
    embed.add_field(name="Utilities", value=utility_commands, inline=False)

    await ctx.send(embed=embed)

@bot.command(name='styles') # Styles command
async def styles(ctx):
    """Show available styles"""
    embed = discord.Embed(
        title="🎨 Available Chat Styles",
        description="Choose a style that suits your needs:",
        color=discord.Color.blue()
    )
    
    for style, description in AVAILABLE_STYLES.items():
        embed.add_field(
            name=f"{style.capitalize()} Style",
            value=f"{description}\n*Use: `!ask set_setting style {style}`*",
            inline=False
        )
    
    embed.set_footer(text="Current style: " + get_user_settings(ctx.author.id)["style"])
    await ctx.send(embed=embed)

@bot.command(name='settings') # Settings command
async def settings(ctx):
    """Show current settings"""
    settings = get_user_settings(ctx.author.id)
    
    embed = discord.Embed(
        title="⚙️ Your Current Settings",
        color=discord.Color.blue()
    )
    
    settings_info = {
        "Style": f"{settings['style'].capitalize()} mode",
        "Temperature": f"{settings['temperature']} (affects response creativity)",
        "Max Tokens": f"{settings['max_tokens']} (maximum response length)",
        "Language": settings['language']
    }
    
    for setting, value in settings_info.items():
        embed.add_field(name=setting, value=value, inline=False)
    
    embed.set_footer(text="Use !ask set_setting [setting] [value] to change settings")
    await ctx.send(embed=embed)

@bot.command(name='set') # Set command
async def set_setting(ctx, setting: str = None, value: str = None):
    """Change a setting"""
    if not setting or not value:
        await ctx.send("Usage: !set <setting> <value>")
        return

    settings = get_user_settings(ctx.author.id)
    setting = setting.lower()

    if setting not in DEFAULT_SETTINGS:
        await ctx.send(f"Invalid setting. Available settings: {', '.join(DEFAULT_SETTINGS.keys())}")
        return

    try:
        if setting == "temperature":
            value = float(value)
            if not 0 <= value <= 1:
                raise ValueError("Temperature  between 0 and 1")
        elif setting == "max_tokens":
            value = int(value)
            if not 100 <= value <= 2000:
                raise ValueError("Max tokens between 100 and 2000")
        elif setting == "style":
            value = value.lower()
            if value not in AVAILABLE_STYLES:
                raise ValueError(f"Style must be one of: {', '.join(AVAILABLE_STYLES.keys())}")

        settings[setting] = value
        user_settings[str(ctx.author.id)] = settings
        save_settings()
        
        if setting == "style":
            await ctx.send(f"✅ Style set to: {value} ({AVAILABLE_STYLES[value]})")
        else:
            await ctx.send(f"✅ {setting} has been set to {value}")
    except ValueError as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='reset') # Reset command
async def reset_settings(ctx):
    """Reset settings to default"""
    user_settings[str(ctx.author.id)] = DEFAULT_SETTINGS.copy()
    save_settings()
    await ctx.send("✅ Settings have been reset to default")

@bot.command(name='clear') # Clear command
async def clear_conversation(ctx):
    """Clear the conversation history"""
    conv = get_conversation(ctx.author.id, ctx.channel.id)
    conv.clear()
    await ctx.send("✨ Conversation history has been cleared!")

@bot.command(name='summarize') # Summarize command
async def summarize_conversation(ctx):
    """Summarize the current conversation"""
    conv = get_conversation(ctx.author.id, ctx.channel.id)
    if not conv.history:
        await ctx.send("No conversation history to summarize!")
        return

    async with ctx.typing():
        try:
            # summary prompt
            history_text = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['parts'][0]}" 
                for msg in conv.history
            ])
            
            prompt = f"""Please provide a brief summary of this conversation:

{history_text}

Focus on the main points discussed and key conclusions."""
            
            response = model.generate_content(prompt) # Generate
            summary = get_response_text(response) # Get response t
            
            if not summary:
                await ctx.send("❌ Failed to generate summary. Please try again.")
                return

            if len(summary) > 4096:  # Limit to 4096 chars (discord)
                summary = summary[:4093] + "..."
            
            embed = discord.Embed(
                title="Conversation Summary",
                description=summary,
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed) # Send embed
        except Exception as e:
            await ctx.send(f"❌ Error generating summary: {str(e)}") # Error

@bot.command(name='ask') # Ask command
async def ask(ctx, *, question=None):
    """Ask a question to the AI"""
    if not question:
        await ctx.send("Give me a question! : !ask <your question>")
        return

    if ctx.message.id in message_history:
        return

    message_history[ctx.message.id] = True
    settings = get_user_settings(ctx.author.id)
    
    async with ctx.typing(): 
        try:
            # Get conversation 
            conv_key = f"{ctx.author.id}_{ctx.channel.id}"
            if conv_key not in conversations:
                conversations[conv_key] = Conversation()
            conv = conversations[conv_key]
            
            style_prompt = get_style_prompt(settings["style"])
            
            # Add user message to history before generate any response (work lo? :v dunno why)
            conv.add_message("user", question)

            # image attach
            if ctx.message.attachments:
                try:
                    image_parts = []
                    total_size = 0
                    
                    for attachment in ctx.message.attachments:
                        if attachment.content_type in SUPPORTED_IMAGE_TYPES:
                            # Check file size
                            if total_size + attachment.size > MAX_IMAGE_SIZE:
                                await ctx.send("⚠️ Total image size too large.")
                                return
                            
                            image_data = await attachment.read()
                            total_size += len(image_data)
                            
                            image_parts.append({
                                "mime_type": attachment.content_type,
                                "data": image_data
                            })
                    
                    if image_parts:
                        # Use Gemini Pro Vision 
                        vision_model = genai.GenerativeModel('gemini-pro-vision')
                        prompt = [{"text": get_enhanced_prompt(question, style_prompt, conv)}] 
                        prompt.extend(image_parts)
                        
                        response = vision_model.generate_content(prompt)
                        response_text = get_response_text(response)
                        
                        if not response_text:
                            await ctx.send("❌ I couldn't analyze the image(s). Please try again.")
                            return
                        
                        # Process image response ( style)
                        is_casual = settings["style"] in ["friendly", "creative"]
                        final_response = process_image_response(response_text, is_casual)
                        
                        #  embed for image response
                        embed = discord.Embed(
                            title="🖼️ Image Analysis",
                            description=final_response,
                            color=discord.Color.blue()
                        )
                        
                        # Add thumbnail 
                        if ctx.message.attachments:
                            embed.set_thumbnail(url=ctx.message.attachments[0].url)
                        
                        await ctx.send(embed=embed)
                        return
                
                except Exception as e:
                    await ctx.send(f"❌ Error processing image: {str(e)}")
                    return
            
            # text based
            chat = model.start_chat(history=conv.get_messages())
            
            #  get style config
            style_config = get_style_config(settings["style"])
            config = genai.types.GenerationConfig(
                temperature=style_config["temperature"],
                top_p=style_config["top_p"],
                top_k=40,
                max_output_tokens=settings["max_tokens"],
                candidate_count=1
            )

            # enhanced prompt
            enhanced_prompt = get_enhanced_prompt(question, style_prompt, conv)
            
            #  response
            chat = model.start_chat(history=conv.get_messages()) # Start chat
            response = chat.send_message( 
                enhanced_prompt,
                generation_config=config
            )

            # Process response
            response_text = get_response_text(response)
            if not response_text:
                await ctx.send("❌ I couldn't generate a proper response.")
                return

            # Add bot response to conversation history (gud fixed)
            conv.add_message("assistant", response_text)

            # Create embed 
            if any(keyword in question.lower() for keyword in [
                "write code", "generate code", "create a program", "write a function",
                "write a class", "implement", "code example", "write script",
                "programming", "function to", "class that", "code for"
            ]):
                # code responses (:3)
                embed = discord.Embed(
                    title="💻 Generated Code",
                    color=discord.Color.green()
                )

                # Split into code blocks and explanation
                parts = response_text.split("```")
                
                # Add explanation before code blocks
                if parts[0].strip():
                    # Limit  length
                    explanation = parts[0].strip()[:1000]  # Limit to 1000 chars
                    embed.description = explanation

                # Process code blocks
                for i in range(1, len(parts), 2):
                    if i < len(parts):
                        # get lang and code
                        block = parts[i].strip()
                        if '\n' in block:
                            lang, *code_lines = block.split('\n')   # Split into lang and code
                            code = '\n'.join(code_lines)
                        else:
                            lang = 'python'  # default lang
                            code = block

                        # Split code into smaller parts if too long
                        if len(code) > 1024:
                            code_parts = [code[j:j+800] for j in range(0, len(code), 800)]  # Split into 800-char parts
                            for k, part in enumerate(code_parts): # Add each part as a field
                                field_value = f"```{lang}\n{part}\n```"
                                if len(field_value) <= 1024:  #    length
                                    embed.add_field( 
                                        name=f"Code Part {k+1}", # Add part number
                                        value=field_value,
                                        inline=False
                                    )
                        else:
                            field_value = f"```{lang}\n{code}\n```"
                            if len(field_value) <= 1024:  # Limit to 1024 chars verify field length
                                embed.add_field(
                                    name=f"Code",
                                    value=field_value,
                                    inline=False
                                )

                #  additional info for res
                if len(parts) > 2 and parts[-1].strip(): # Add additional info 
                    additional_info = parts[-1].strip()[:1000]  # Limit to 1000 chars
                    embed.add_field(
                        name="Additional Information",
                        value=additional_info,
                        inline=False
                    )

            else:
                # non-code responses
                embed = discord.Embed(
                    title=f"{get_response_title(question, settings['style'])}", 
                    color=discord.Color.blue()
                )

                if len(response_text) > 4096: # Limit to 4096 chars
                    # Split into smaller , ensuring each is under 1024
                    chunks = [response_text[i:i+800] for i in range(0, len(response_text), 800)] # Split into 800-char parts
                    for i, chunk in enumerate(chunks): # Add each part as a field
                        embed.add_field(
                            name=f"Part {i+1}" if i > 0 else "Response",
                            value=chunk,
                            inline=False
                        )
                else:
                    embed.description = response_text[:4096]  # Limit to 4096 chars for description

            # make sure we have 1 field
            if not embed.description and len(embed.fields) == 0: # Add empty field if no description
                embed.description = "I generated a response but couldn't format it properly. Please try asking in a different way."

            await ctx.send(embed=embed) # Send embed

        except Exception as e: # Error handling
            error_message = str(e) # Get error message
            print(f"Error details: {error_message}")  # Log the full error
            if "quota" in error_message.lower():
                await ctx.send("❌ API quota exceeded.")
            elif "safety" in error_message.lower():
                await ctx.send("❌ I cannot provide a response to that type of question")
            else:
                await ctx.send(f"❌ An error occurred: {str(e)}\nPlease try asking in a different way.")

@bot.command(name='reset_conversation') 
async def reset_conversation(ctx):
    """Reset the conversation context"""
    conv = get_conversation(ctx.author.id, ctx.channel.id)
    conv.clear()
    await ctx.send("The conversation has been reset.")

@bot.command(name='analyze') # Analyze command
async def analyze_image(ctx):
    """Analyze an attached image"""
    if not ctx.message.attachments:
        await ctx.send("Please attach an image to analyze! : !analyze + attach an image")
        return

    async with ctx.typing(): 
        try:
            # Handle image attachments
            image_parts = []
            for attachment in ctx.message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']): # Check file type
                    try:
                        image_data = await attachment.read() # Read image data
                        image_parts.append({ # Add image parts
                            "mime_type": attachment.content_type, # Get content type
                            "data": image_data
                        })
                    except Exception as e: # Error handling
                        await ctx.send(f"❌ Error processing image: {str(e)}")
                        return

            if not image_parts: # Check if no image parts
                await ctx.send("❌ Please provide a valid image ")
                return

            # enchance prompt for image analysis (promt from chat gpt :)) )
            analysis_prompt = [
                {
                    "text": """Please provide a detailed analysis of this image. Include:
1. Description of what's in the image
2. Notable details and features
3. Colors, composition, and style
4. Any text or symbols if present
5. Context or setting
6. Technical aspects (if relevant)

Please be specific and thorough in your analysis."""
                }
            ]
            analysis_prompt.extend(image_parts)

            # Use Gemini 1.5 Flash
            vision_model = genai.GenerativeModel('gemini-1.5-flash')
            response = vision_model.generate_content(analysis_prompt)
            
            # Process and send response
            response_text = get_response_text(response)
            if not response_text:
                await ctx.send("❌ Failed to analyze the image. Please try again.")
                return

            # embed now :3 anddd end
            embed = discord.Embed(
                title="📸 Image Analysis",
                description=response_text,
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

        except Exception as e: 
            error_message = str(e)
            if "safety" in error_message.lower():
                await ctx.send("❌ I cannot analyze this type of image. Please try a different one.")
            else:
                print(f"Error details: {error_message}")
                await ctx.send("❌ An error occurred while analyzing the image. Please try again.")

bot.run(os.getenv('DISCORD_TOKEN')) 
