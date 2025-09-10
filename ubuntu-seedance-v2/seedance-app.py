import gradio as gr
import os
import requests
import json
import time
import base64
from dotenv import load_dotenv
from PIL import Image
import io

# Load environment variables
load_dotenv()

# API Configuration
ARK_API_KEY = os.getenv("ARK_API_KEY")
ARK_BASE_URL = os.getenv("ARK_BASE_URL")
MODEL_PRO = os.getenv("MODEL_SEEDANCE_PRO_API")
MODEL_LITE_T2V = os.getenv("MODEL_SEEDANCE_LITE_T2V_API")
MODEL_LITE_I2V = os.getenv("MODEL_SEEDANCE_LITE_I2V_API")

def call_seedance_api(model, payload):
    """Call Seedance API with proper error handling"""
    if not ARK_API_KEY or not ARK_BASE_URL:
        return {"error": "API credentials not configured"}
    
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{ARK_BASE_URL}/chat/completions"
    
    api_payload = {
        "model": model,
        "messages": [{"role": "user", "content": json.dumps(payload)}],
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=api_payload, timeout=300)
        response.raise_for_status()
        
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"response": content, "raw": True}
        else:
            return {"error": "No response from API"}
            
    except requests.exceptions.Timeout:
        return {"error": "API request timed out (300s limit)"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def image_to_base64(image):
    """Convert PIL image to base64 string"""
    if image is None:
        return None
    
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def generate_text_video(prompt, model_choice):
    """Generate video from text prompt"""
    if not prompt.strip():
        return None, "❌ Please enter a text prompt"
    
    if not ARK_API_KEY:
        return None, "❌ API key not configured. Please check environment variables."
    
    # Select model
    model = MODEL_PRO if model_choice == "pro" else MODEL_LITE_T2V
    
    if not model:
        return None, f"❌ {model_choice} model not configured"
    
    # Create payload for Seedance API
    payload = {
        "prompt": prompt,
        "type": "text_to_video",
        "model": model_choice
    }
    
    # Call API
    result = call_seedance_api(model, payload)
    
    if "error" in result:
        return None, f"❌ Generation failed: {result['error']}"
    
    # Check for video URL in response
    if "video_url" in result:
        return result["video_url"], f"✅ Video generated successfully!\nModel: {model_choice.upper()}\nPrompt: {prompt}"
    elif "raw" in result:
        return None, f"✅ API response received!\nModel: {model_choice.upper()}\nPrompt: {prompt}\n\nResponse: {result['response']}"
    elif "task_id" in result:
        return None, f"🔄 Video generation started!\nModel: {model_choice.upper()}\nPrompt: {prompt}\nTask ID: {result['task_id']}\n\nNote: This is an async task. In a production environment, you would poll for completion."
    else:
        return None, f"✅ API call successful!\nModel: {model_choice.upper()}\nPrompt: {prompt}\n\nResponse: {json.dumps(result, indent=2)}"

def generate_image_video(image, prompt):
    """Generate video from image and optional prompt"""
    if image is None:
        return None, "❌ Please upload an image"
    
    if not ARK_API_KEY:
        return None, "❌ API key not configured. Please check environment variables."
    
    if not MODEL_LITE_I2V:
        return None, "❌ Image-to-Video model not configured"
    
    # Convert image to base64
    image_b64 = image_to_base64(image)
    
    # Create payload for Seedance API
    payload = {
        "image": image_b64,
        "prompt": prompt or "Generate a video from this image",
        "type": "image_to_video"
    }
    
    # Call API
    result = call_seedance_api(MODEL_LITE_I2V, payload)
    
    if "error" in result:
        return None, f"❌ Generation failed: {result['error']}"
    
    # Check for video URL in response
    if "video_url" in result:
        return result["video_url"], f"✅ Video generated successfully!\nModel: Image-to-Video\nPrompt: {prompt or 'No prompt provided'}"
    elif "raw" in result:
        return None, f"✅ API response received!\nModel: Image-to-Video\nPrompt: {prompt or 'No prompt provided'}\n\nResponse: {result['response']}"
    elif "task_id" in result:
        return None, f"🔄 Video generation started!\nModel: Image-to-Video\nPrompt: {prompt or 'No prompt provided'}\nTask ID: {result['task_id']}\n\nNote: This is an async task. In a production environment, you would poll for completion."
    else:
        return None, f"✅ API call successful!\nModel: Image-to-Video\nPrompt: {prompt or 'No prompt provided'}\n\nResponse: {json.dumps(result, indent=2)}"

def test_api_connection():
    """Test API connection and configuration"""
    if not ARK_API_KEY:
        return "❌ ARK_API_KEY not configured"
    
    if not ARK_BASE_URL:
        return "❌ ARK_BASE_URL not configured"
    
    # Test API endpoint
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Simple test call
        test_payload = {
            "model": MODEL_PRO or "test-model",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1,
            "stream": False
        }
        
        response = requests.post(f"{ARK_BASE_URL}/chat/completions", 
                               headers=headers, 
                               json=test_payload, 
                               timeout=10)
        
        if response.status_code == 200:
            return "✅ API connection successful!"
        elif response.status_code == 401:
            return "❌ Authentication failed - check API key"
        elif response.status_code == 403:
            return "❌ Access forbidden - check permissions"
        else:
            return f"⚠️ API responded with status {response.status_code}"
            
    except requests.exceptions.Timeout:
        return "❌ API connection timeout"
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to API endpoint"
    except Exception as e:
        return f"❌ Connection test failed: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Seedance V2 - Video Generation", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎬 Seedance V2 - AI Video Generation")
    gr.Markdown("**Deploy on BytePlus ECS Ubuntu Server**")
    
    # API Status
    api_status = "✅ Connected" if ARK_API_KEY and ARK_BASE_URL else "❌ Not Configured"
    gr.Markdown(f"**API Status:** {api_status}")
    
    if not ARK_API_KEY or not ARK_BASE_URL:
        gr.Markdown("⚠️ **Warning:** API credentials not configured. Please check environment variables.")
    
    with gr.Tab("🔧 API Configuration"):
        gr.Markdown("### Current Configuration")
        
        api_key_display = f"{'*' * 20}...{ARK_API_KEY[-4:] if ARK_API_KEY else 'Not Set'}"
        
        gr.Textbox(label="API Key", value=api_key_display, interactive=False)
        gr.Textbox(label="Base URL", value=ARK_BASE_URL or "Not Set", interactive=False)
        gr.Textbox(label="Pro Model", value=MODEL_PRO or "Not Set", interactive=False)
        gr.Textbox(label="Lite T2V Model", value=MODEL_LITE_T2V or "Not Set", interactive=False)
        gr.Textbox(label="Lite I2V Model", value=MODEL_LITE_I2V or "Not Set", interactive=False)
        
        test_btn = gr.Button("🔍 Test API Connection", variant="secondary")
        test_output = gr.Textbox(label="Connection Test Result", lines=3)
        test_btn.click(test_api_connection, outputs=test_output)
    
    with gr.Tab("✍️ Text to Video"):
        with gr.Row():
            with gr.Column():
                text_prompt = gr.Textbox(
                    label="Text Prompt",
                    placeholder="Enter your video description...",
                    lines=3,
                    value="A beautiful sunset over the ocean with gentle waves, cinematic lighting"
                )
                model_choice = gr.Radio(
                    choices=[("Pro Model", "pro"), ("Lite Model", "lite")],
                    value="pro",
                    label="Model Selection"
                )
                t2v_btn = gr.Button("🎬 Generate Video", variant="primary", size="lg")
            
            with gr.Column():
                t2v_output = gr.Video(label="Generated Video", height=400)
                t2v_status = gr.Textbox(label="Status", lines=8, max_lines=15)
        
        t2v_btn.click(
            fn=generate_text_video,
            inputs=[text_prompt, model_choice],
            outputs=[t2v_output, t2v_status],
            show_progress=True
        )
    
    with gr.Tab("🖼️ Image to Video"):
        with gr.Row():
            with gr.Column():
                input_image = gr.Image(
                    label="Upload Image",
                    type="pil",
                    height=300
                )
                image_prompt = gr.Textbox(
                    label="Motion Prompt (Optional)",
                    placeholder="Describe the motion you want to see...",
                    lines=3,
                    value="Make the scene come alive with natural motion"
                )
                i2v_btn = gr.Button("🎬 Generate Video", variant="primary", size="lg")
            
            with gr.Column():
                i2v_output = gr.Video(label="Generated Video", height=400)
                i2v_status = gr.Textbox(label="Status", lines=8, max_lines=15)
        
        i2v_btn.click(
            fn=generate_image_video,
            inputs=[input_image, image_prompt],
            outputs=[i2v_output, i2v_status],
            show_progress=True
        )
    
    with gr.Tab("ℹ️ About"):
        gr.Markdown("""
        ## Seedance V2 - AI Video Generation
        
        This application provides a web interface for BytePlus Seedance API, enabling:
        
        - **Text-to-Video Generation**: Create videos from textual descriptions
        - **Image-to-Video Generation**: Animate static images with motion
        - **Multiple Model Support**: Choose between Pro and Lite models
        - **Real-time Status Updates**: Monitor generation progress
        
        ### Models Available:
        - **Seedance Pro**: High-quality video generation with advanced features
        - **Seedance Lite T2V**: Fast text-to-video generation
        - **Seedance Lite I2V**: Fast image-to-video generation
        
        ### Usage Tips:
        - Use descriptive prompts for better results
        - Pro model provides higher quality but may take longer
        - Lite models are faster for quick iterations
        - Upload clear, high-contrast images for I2V generation
        
        ---
        **Deployed on BytePlus ECS** | **Powered by Seedance API**
        """)

if __name__ == "__main__":
    print("🚀 Starting Seedance V2 Application...")
    print(f"API Key: {'Configured' if ARK_API_KEY else 'Missing'}")
    print(f"Base URL: {ARK_BASE_URL}")
    print(f"Pro Model: {MODEL_PRO}")
    print(f"Lite T2V Model: {MODEL_LITE_T2V}")
    print(f"Lite I2V Model: {MODEL_LITE_I2V}")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )