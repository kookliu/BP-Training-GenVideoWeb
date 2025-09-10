import gradio as gr
import os
from dotenv import load_dotenv

load_dotenv()

ARK_API_KEY = os.getenv("ARK_API_KEY")
ARK_BASE_URL = os.getenv("ARK_BASE_URL") 
MODEL_PRO = os.getenv("MODEL_SEEDANCE_PRO_API")

def test_api_config():
    if ARK_API_KEY:
        return f"✅ API Key: {ARK_API_KEY[:10]}...{ARK_API_KEY[-4:]}\n🌐 Base URL: {ARK_BASE_URL}\n🤖 Pro Model: {MODEL_PRO}\n\nStatus: API Configured Successfully!"
    else:
        return "❌ API Key: Not configured\n\nPlease check environment variables."

def generate_text_video(prompt, model_choice):
    if not prompt.strip():
        return None, "❌ Please enter a text prompt"
    
    return None, f"✅ Test Mode Active\n🎬 Would generate video with:\nPrompt: {prompt}\nModel: {model_choice} model\n\nAPI Integration: Ready for real implementation!"

with gr.Blocks(title="Seedance V2 - Simple Test") as demo:
    gr.Markdown("# 🎬 Seedance V2 - AI Video Generation (Test Mode)")
    gr.Markdown("**GitHub Integration Working - Ready for Full API Implementation**")
    
    with gr.Tab("🔧 API Configuration Test"):
        test_btn = gr.Button("🔍 Test API Configuration", variant="primary")
        test_output = gr.Textbox(label="Configuration Status", lines=8)
        test_btn.click(test_api_config, outputs=test_output)
    
    with gr.Tab("✍️ Text to Video Test"):
        text_prompt = gr.Textbox(
            label="Text Prompt", 
            value="A beautiful sunset over the ocean with gentle waves",
            lines=2
        )
        model_choice = gr.Radio(
            [("Pro Model", "pro"), ("Lite Model", "lite")], 
            value="pro",
            label="Model Selection"
        )
        gen_btn = gr.Button("🎬 Test Generate Video", variant="primary")
        video_output = gr.Video(label="Generated Video")
        status_output = gr.Textbox(label="Status", lines=5)
        gen_btn.click(generate_text_video, inputs=[text_prompt, model_choice], outputs=[video_output, status_output])
    
    with gr.Tab("ℹ️ About"):
        gr.Markdown("""
        ## GitHub Integration Success! 🎉
        
        This simplified version demonstrates:
        - ✅ GitHub file hosting and download
        - ✅ Environment variable configuration
        - ✅ Gradio 5.42 compatibility 
        - ✅ Service deployment on BytePlus ECS
        
        The full API integration is ready to be enabled by updating to the complete application.
        
        ---
        **Updated for Gradio 5.42 Compatibility**
        """)

if __name__ == "__main__":
    print("🚀 Starting Seedance V2 Simple Test Application...")
    print(f"API Key: {'Configured' if ARK_API_KEY else 'Missing'}")
    print(f"Base URL: {ARK_BASE_URL}")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)