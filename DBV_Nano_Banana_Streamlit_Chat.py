# Enhanced DBV Nano Banana Streamlit Chat Application
# Installation: pip install streamlit pillow google-genai
# Run: streamlit run enhanced_nano_banana_chat.py
# Generated with the help of Claude Sonnet 4 and Gemini 2.5

import os
import io
import json
import mimetypes
from datetime import datetime
from typing import List, Dict, Any

import streamlit as st
from PIL import Image

from google import genai
from google.genai import types

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="DBV Nano Banana Chat", 
    page_icon="🍌", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS STYLING ====================
st.markdown("""
<style>
/* Hide Streamlit default elements */
.stAppDeployButton { display: none !important; }
[data-testid="stMainMenu"] { display: none !important; }

/* Enhanced chat styling */
.stChat > div {
    background: linear-gradient(90deg, #f8f9fa 0%, #ffffff 100%);
    border-radius: 12px;
    padding: 1rem;
    margin: 0.5rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stChatMessage[data-testid="chat-message-user"] {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    border-left: 4px solid #2196f3;
}

.stChatMessage[data-testid="chat-message-assistant"] {
    background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
    border-left: 4px solid #9c27b0;
}

/* Improved metrics */
.metric-container {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Better file upload styling */
.stFileUploader > div {
    border: 2px dashed #ccc;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}

/* Custom button styling */
.stButton > button {
    border-radius: 8px;
    border: none;
    padding: 0.5rem 1rem;
    font-weight: 500;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

# ==================== UTILITY FUNCTIONS ====================
@st.cache_resource
def get_gemini_client(api_key: str) -> genai.Client:
    """Initialize and cache Gemini client"""
    return genai.Client(api_key=api_key)

def initialize_session_state():
    """Initialize all session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "total_cost" not in st.session_state:
        st.session_state.total_cost = 0.0
    if "image_count" not in st.session_state:
        st.session_state.image_count = 0
    if "generation_count" not in st.session_state:
        st.session_state.generation_count = 0

def enhance_prompt(prompt: str, style_preset: str, aspect_ratio: str) -> str:
    """Enhance user prompt with style and aspect ratio preferences"""
    style_prompts = {
        "Photorealistic": "A photorealistic, high-resolution image with detailed lighting and textures. Shot with professional camera equipment.",
        "Artistic": "An artistic interpretation with creative composition and enhanced colors.",
        "Cartoon": "A cartoon-style illustration with bold colors and simplified forms.",
        "Sketch": "A detailed pencil sketch with fine line work and shading.",
        "Digital Art": "A modern digital artwork with vibrant colors and contemporary style.",
        "Minimalist": "A clean, minimalist design with simple shapes and limited color palette."
    }
    
    enhanced_prompt = prompt
    
    if style_preset != "Default":
        enhanced_prompt = f"{style_prompts[style_preset]} {enhanced_prompt}"
    
    if aspect_ratio != "1:1":
        enhanced_prompt = f"{enhanced_prompt} The image should be in {aspect_ratio} aspect ratio format."
    
    return enhanced_prompt

def export_chat_history() -> str:
    """Export chat history as JSON"""
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "total_cost": st.session_state.total_cost,
        "image_count": st.session_state.image_count,
        "generation_count": st.session_state.generation_count,
        "messages": []
    }
    
    for message in st.session_state.messages:
        export_message = {
            "role": message["role"],
            "timestamp": message.get("timestamp", datetime.now().isoformat()),
            "content": []
        }
        
        for part in message["content"]:
            if part["type"] == "text":
                export_message["content"].append({
                    "type": "text",
                    "data": part["data"]
                })
            elif part["type"] == "image":
                export_message["content"].append({
                    "type": "image",
                    "caption": part.get("caption", ""),
                    "note": "Image data not exported"
                })
        
        export_data["messages"].append(export_message)
    
    return json.dumps(export_data, indent=2)

def save_image_with_metadata(image_data: bytes, mime_type: str, output_dir: str, 
                           prompt: str = "", style: str = "") -> str:
    """Save image with metadata and return filename"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = mimetypes.guess_extension(mime_type) or ".png"
    filename = f"nanobanana_{ts}_{st.session_state.generation_count}{ext}"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(image_data)
    
    # Save metadata
    metadata = {
        "filename": filename,
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "style": style,
        "mime_type": mime_type,
        "size_bytes": len(image_data)
    }
    
    metadata_file = filepath.replace(ext, "_metadata.json")
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return filepath

# ==================== MAIN APPLICATION ====================
def main():
    # Initialize session state
    initialize_session_state()
    
    # Page title with emoji
    st.title("🍌 DBV Nano Banana Chat")
    st.markdown("### *Enhanced Gemini 2.5 Flash Image Generation*")
    
    # ==================== SIDEBAR CONFIGURATION ====================
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key_input = st.text_input(
            "GEMINI_API_KEY", 
            type="password", 
            help="Your Google AI API key (not stored permanently)"
        )
        
        set_env = st.checkbox("Set as environment variable", value=True)
        
        # Output directory
        output_dir = st.text_input("Output Directory", value="outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        st.divider()
        
        # ==================== GENERATION SETTINGS ====================
        st.subheader("🎨 Generation Settings")
        
        style_preset = st.selectbox(
            "Style Preset",
            ["Default", "Photorealistic", "Artistic", "Cartoon", "Sketch", "Digital Art", "Minimalist"],
            help="Choose a visual style for image generation"
        )
        
        aspect_ratio = st.selectbox(
            "Aspect Ratio",
            ["1:1", "16:9", "4:3", "3:4", "9:16"],
            help="Select the desired aspect ratio for generated images"
        )
        
        st.divider()
        
        # ==================== CHAT MANAGEMENT ====================
        st.subheader("💬 Chat Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.total_cost = 0.0
                st.session_state.image_count = 0
                st.session_state.generation_count = 0
                st.rerun()
        
        with col2:
            if st.button("📤 Export", use_container_width=True) and st.session_state.messages:
                chat_export = export_chat_history()
                st.download_button(
                    label="💾 Download JSON",
                    data=chat_export,
                    file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        st.divider()
        
        # ==================== COST TRACKING ====================
        st.subheader("💰 Session Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Cost", f"${st.session_state.total_cost:.4f}")
            st.metric("Images Generated", st.session_state.image_count)
        
        with col2:
            st.metric("Generations", st.session_state.generation_count)
            if st.session_state.messages:
                st.metric("Messages", len(st.session_state.messages))
        
        # Cost information
        show_cost_info = st.checkbox("Show detailed cost info", value=True)
        
        if show_cost_info:
            st.info("💡 **Cost Estimation**: ~$0.039 per generated image")
    
    # ==================== MAIN CHAT INTERFACE ====================
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            for part in message["content"]:
                if part["type"] == "text":
                    st.markdown(part["data"])
                elif part["type"] == "image":
                    # Enhanced image display with metadata
                    if isinstance(part["data"], str) and os.path.exists(part["data"]):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.image(
                                part["data"], 
                                caption=part.get("caption", ""),
                                use_container_width=True
                            )
                        
                        with col2:
                            try:
                                file_size = os.path.getsize(part["data"]) / 1024  # KB
                                st.metric("Size", f"{file_size:.1f} KB")
                                
                                with open(part["data"], "rb") as f:
                                    st.download_button(
                                        "⬇️ Download",
                                        data=f.read(),
                                        file_name=os.path.basename(part["data"]),
                                        mime="image/png",
                                        use_container_width=True
                                    )
                            except:
                                st.error("File not found")
                    else:
                        st.image(part["data"], use_container_width=True)
    
    # ==================== USER INPUT SECTION ====================
    
    # Reference images upload
    ref_images = st.file_uploader(
        "📎 Reference Images (optional, up to 3)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        help="Upload reference images to guide the generation"
    )
    
    if ref_images and len(ref_images) > 3:
        st.warning("⚠️ Only the first 3 images will be used.")
        ref_images = ref_images[:3]
    
    # Chat input
    if prompt := st.chat_input("✨ What would you like to generate?"):
        # Validate API key
        api_key = api_key_input.strip()
        if not api_key:
            st.error("🔑 Please configure your GEMINI_API_KEY in the sidebar.")
            st.stop()
        
        # Set environment variable if requested
        if set_env:
            os.environ["GEMINI_API_KEY"] = api_key
        
        # Get cached client
        try:
            client = get_gemini_client(api_key)
        except Exception as e:
            st.error(f"❌ Failed to initialize Gemini client: {e}")
            st.stop()
        
        # Enhance prompt with style preferences
        enhanced_prompt = enhance_prompt(prompt, style_preset, aspect_ratio)
        
        # Add user message to chat history
        user_message_content = []
        
        # Add reference images
        if ref_images:
            for uploaded_file in ref_images:
                img_bytes = uploaded_file.getvalue()
                user_message_content.append({
                    "type": "image", 
                    "data": img_bytes,
                    "caption": f"Reference: {uploaded_file.name}"
                })
        
        # Add text prompt
        user_message_content.append({
            "type": "text", 
            "data": f"**Original prompt:** {prompt}\n\n**Enhanced prompt:** {enhanced_prompt}" if enhanced_prompt != prompt else prompt
        })
        
        # Add timestamp to message
        user_message = {
            "role": "user", 
            "content": user_message_content,
            "timestamp": datetime.now().isoformat()
        }
        
        st.session_state.messages.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            for part in user_message_content:
                if part["type"] == "text":
                    st.markdown(part["data"])
                elif part["type"] == "image":
                    st.image(part["data"], caption=part.get("caption", ""), use_container_width=True)
        
        # ==================== API CALL AND RESPONSE ====================
        
        # Prepare API payload
        contents = []
        for message in st.session_state.messages:
            role = message["role"]
            parts = []
            
            for part in message["content"]:
                if part["type"] == "text":
                    # Use enhanced prompt for the latest message
                    text_content = enhanced_prompt if (message == st.session_state.messages[-1] and part == message["content"][-1]) else part["data"]
                    # FIXED: Use keyword argument for text
                    parts.append(types.Part(text=text_content))
                elif part["type"] == "image":
                    if isinstance(part["data"], bytes):
                        img_data = part["data"]
                    else:
                        # Handle file path
                        try:
                            with open(part["data"], "rb") as f:
                                img_data = f.read()
                        except:
                            continue
                    
                    # Convert to PIL Image and then to PNG bytes
                    img = Image.open(io.BytesIO(img_data)).convert("RGB")
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    # FIXED: Use keyword arguments for bytes
                    parts.append(types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"))
            
            contents.append(types.Content(parts=parts, role=role))
        
        # API configuration
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"]
        )
        
        # Generate content with enhanced error handling
        with st.spinner("🎨 Generating your masterpiece..."):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image-preview",
                    contents=contents,
                    config=config,
                )
            except Exception as e:
                error_msg = str(e).lower()
                if "quota" in error_msg or "limit" in error_msg:
                    st.error("⚠️ **API Quota Exceeded**: Please check your usage limits or try again later.")
                elif "key" in error_msg or "auth" in error_msg:
                    st.error("🔑 **Authentication Error**: Please verify your API key is correct and active.")
                elif "safety" in error_msg:
                    st.error("🛡️ **Safety Filter**: Your prompt was blocked by safety filters. Try rephrasing your request.")
                else:
                    st.error(f"❌ **API Error**: {e}")
                st.stop()
        
        # ==================== PROCESS RESPONSE ====================
        
        model_message_content = []
        images_saved = []
        texts = []
        session_cost = 0.0
        
        if hasattr(response, "candidates") and response.candidates:
            for i, cand in enumerate(response.candidates):
                cont = getattr(cand, "content", None)
                if not cont or not getattr(cont, "parts", None):
                    continue
                
                for j, part in enumerate(cont.parts):
                    # Handle images
                    inline_data = getattr(part, "inline_data", None)
                    if inline_data and getattr(inline_data, "data", None):
                        filepath = save_image_with_metadata(
                            inline_data.data,
                            getattr(inline_data, "mime_type", "image/png"),
                            output_dir,
                            prompt,
                            style_preset
                        )
                        images_saved.append(filepath)
                        model_message_content.append({
                            "type": "image", 
                            "data": filepath, 
                            "caption": f"Generated: {os.path.basename(filepath)}"
                        })
                    
                    # Handle text
                    text = getattr(part, "text", None)
                    if text:
                        texts.append(text)
                        model_message_content.append({
                            "type": "text", 
                            "data": text
                        })
        
        # Update session statistics
        if images_saved:
            session_cost = len(images_saved) * 0.039
            st.session_state.total_cost += session_cost
            st.session_state.image_count += len(images_saved)
        
        st.session_state.generation_count += 1
        
        # Display results
        if not images_saved and not texts:
            st.warning("⚠️ **No content generated**. Try a more specific prompt or check your API quotas.")
        else:
            # Add model response to chat history
            model_message = {
                "role": "model", 
                "content": model_message_content,
                "timestamp": datetime.now().isoformat()
            }
            st.session_state.messages.append(model_message)
            
            # Display model response
            with st.chat_message("assistant"):
                for part in model_message_content:
                    if part["type"] == "text":
                        st.markdown(part["data"])
                    elif part["type"] == "image":
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.image(
                                part["data"], 
                                caption=part.get("caption", ""),
                                use_container_width=True
                            )
                        
                        with col2:
                            try:
                                file_size = os.path.getsize(part["data"]) / 1024
                                st.metric("Size", f"{file_size:.1f} KB")
                                
                                with open(part["data"], "rb") as f:
                                    st.download_button(
                                        "⬇️ Download",
                                        data=f.read(),
                                        file_name=os.path.basename(part["data"]),
                                        mime="image/png",
                                        use_container_width=True
                                    )
                            except:
                                st.error("File access error")
            
            # Show session cost update
            if show_cost_info and session_cost > 0:
                st.success(f"✅ **Generation Complete!** Cost: ${session_cost:.4f} | Total Session: ${st.session_state.total_cost:.4f}")

# ==================== APPLICATION ENTRY POINT ====================
if __name__ == "__main__":
    main()
