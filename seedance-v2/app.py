import gradio as gr
import os
import tempfile
import time
import requests
import sys
import io
import base64
import mimetypes
from contextlib import redirect_stdout, redirect_stderr
from PIL import Image
from typing import Optional, Dict, Any, List

# 模型API调用时使用的内部ID常量 - 从环境变量获取，带默认值

MODEL_SEEDANCE_PRO_API = os.getenv("MODEL_SEEDANCE_PRO_API", "seedance-1-0-pro-250528")
MODEL_SEEDANCE_LITE_T2V_API = os.getenv("MODEL_SEEDANCE_LITE_T2V_API", "seedance-1-0-lite-t2v-250428")
MODEL_SEEDANCE_LITE_I2V_API = os.getenv("MODEL_SEEDANCE_LITE_I2V_API", "seedance-1-0-lite-i2v-250428")

class BytePlusVideoClient:
    """BytePlus ModelArk video generation client"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initialize BytePlus video client
        
        Args:
            api_key: BytePlus API key
            base_url: BytePlus API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        
        # Debug: Print API configuration status

        
        if not self.api_key or not self.base_url:
            error_msg = f"API key and base URL are required. Current: API_KEY={'PROVIDED' if self.api_key else 'MISSING'}, BASE_URL={self.base_url or 'MISSING'}"
            raise ValueError(error_msg)
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Model configuration - Updated based on official documentation
        self.models = {
            "text_to_video": {
                "Bytedance-Seedance-1.0-pro": MODEL_SEEDANCE_PRO_API,
                "Bytedance-Seedance-1.0-Lite-t2v": MODEL_SEEDANCE_LITE_T2V_API
            },
            "image_to_video": {
                "Bytedance-Seedance-1.0-pro": MODEL_SEEDANCE_PRO_API, 
                "Bytedance-Seedance-1.0-Lite-i2v": MODEL_SEEDANCE_LITE_I2V_API
            },
            "first_last_frame": {
                "Bytedance-Seedance-1.0-Lite-i2v": MODEL_SEEDANCE_LITE_I2V_API
            },
            "image_refs": {
                "Bytedance-Seedance-1.0-Lite-i2v": MODEL_SEEDANCE_LITE_I2V_API
            }
        }
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 format"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def create_text_to_video_task(self, 
                                  prompt: str, 
                                  model: str = "Bytedance-Seedance-1.0-Lite-t2v",
                                  resolution: str = "720p",
                                  duration: int = 5,
                                  ratio: str = "16:9",
                                  seed: Optional[int] = None,
                                  watermark: bool = True) -> Dict[str, Any]:
        """Create text-to-video task"""
        
        # Build complete prompt with parameters
        full_prompt = f"{prompt} --resolution {resolution} --duration {duration} --ratio {ratio}"
        
        # Add seed parameter if provided
        if seed is not None:
            full_prompt += f" --seed {seed}"
        
        # Add watermark parameter
        if not watermark:
            full_prompt += " --no-watermark"
        
        # Get model ID from model name
        model_id = self.models["text_to_video"].get(model, self.models["text_to_video"]["Bytedance-Seedance-1.0-Lite-t2v"])
        
        payload = {
            "model": model_id,
            "content": [
                {
                    "type": "text",
                    "text": full_prompt
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/contents/generations/tasks",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to create text-to-video task: {str(e)}"}
    
    def create_image_to_video_task(self, 
                                   image_url: str = None,
                                   image_path: str = None,
                                   prompt: str = "",
                                   model: str = "Bytedance-Seedance-1.0-Lite-i2v",
                                   resolution: str = "720p", 
                                   duration: int = 5,
                                   ratio: str = "16:9",
                                   seed: Optional[int] = None,
                                   watermark: bool = True) -> Dict[str, Any]:
        """Create image-to-video task"""
        
        content = []
        
        # 添加文本prompt（如果提供）
        # Note: image-to-video only supports --ratio adaptive
        if prompt:
            full_prompt = f"{prompt} --resolution {resolution} --duration {duration} --ratio adaptive"
        else:
            # 只有参数的情况
            full_prompt = f"--resolution {resolution} --duration {duration} --ratio adaptive"
        
        # Add seed parameter if provided
        if seed is not None:
            full_prompt += f" --seed {seed}"
        
        # Add watermark parameter
        if not watermark:
            full_prompt += " --no-watermark"
            
        content.append({
            "type": "text",
            "text": full_prompt
        })
        
        # 添加图片 - 支持URL或本地文件路径
        if image_url:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            })
        elif image_path:
            # 将本地图片转换为base64
            try:
                base64_image = self.encode_image_to_base64(image_path)
                # 检测图片格式
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type or not mime_type.startswith('image/'):
                    mime_type = 'image/jpeg'  # 默认为jpeg
                
                data_url = f"data:{mime_type};base64,{base64_image}"
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": data_url
                    }
                })
            except Exception as e:
                return {"error": f"Failed to encode image: {str(e)}"}
        else:
            return {"error": "Either image_url or image_path must be provided"}
        
        # Get model ID from model name
        model_id = self.models["image_to_video"].get(model, self.models["image_to_video"]["Bytedance-Seedance-1.0-Lite-i2v"])
        
        payload = {
            "model": model_id,
            "content": content
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/contents/generations/tasks",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.text
                except:
                    pass
            return {"error": f"Failed to create image-to-video task: {error_detail}"}
    
    def create_first_last_frame_task(self, 
                                     first_frame_url: str = None,
                                     first_frame_path: str = None,
                                     last_frame_url: str = None,
                                     last_frame_path: str = None,
                                     prompt: str = "",
                                     model: str = "Bytedance-Seedance-1.0-Lite-i2v",
                                     resolution: str = "720p", 
                                     duration: int = 5,
                                     cf: bool = False,
                                     seed: Optional[int] = None,
                                     watermark: bool = True) -> Dict[str, Any]:
        """Create first-last frame video task"""
        
        content = []
        
        # Build prompt with parameters
        if prompt:
            full_prompt = f"{prompt} --rs {resolution} --dur {duration} --cf {str(cf).lower()}"
        else:
            full_prompt = f"--rs {resolution} --dur {duration} --cf {str(cf).lower()}"
        
        # Add seed parameter if provided
        if seed is not None:
            full_prompt += f" --seed {seed}"
        
        # Add watermark parameter
        if not watermark:
            full_prompt += " --no-watermark"
            
        content.append({
            "type": "text",
            "text": full_prompt
        })
        
        # Add first frame
        if first_frame_url:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": first_frame_url
                },
                "role": "first_frame"
            })
        elif first_frame_path:
            try:
                base64_image = self.encode_image_to_base64(first_frame_path)
                mime_type, _ = mimetypes.guess_type(first_frame_path)
                if not mime_type or not mime_type.startswith('image/'):
                    mime_type = 'image/jpeg'
                
                data_url = f"data:{mime_type};base64,{base64_image}"
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": data_url
                    },
                    "role": "first_frame"
                })
            except Exception as e:
                return {"error": f"Failed to encode first frame: {str(e)}"}
        else:
            return {"error": "Either first_frame_url or first_frame_path must be provided"}
        
        # Add last frame
        if last_frame_url:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": last_frame_url
                },
                "role": "last_frame"
            })
        elif last_frame_path:
            try:
                base64_image = self.encode_image_to_base64(last_frame_path)
                mime_type, _ = mimetypes.guess_type(last_frame_path)
                if not mime_type or not mime_type.startswith('image/'):
                    mime_type = 'image/jpeg'
                
                data_url = f"data:{mime_type};base64,{base64_image}"
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": data_url
                    },
                    "role": "last_frame"
                })
            except Exception as e:
                return {"error": f"Failed to encode last frame: {str(e)}"}
        else:
            return {"error": "Either last_frame_url or last_frame_path must be provided"}
        
        # Get model ID - only Lite i2v model is supported for this feature
        model_id = self.models["first_last_frame"].get(model, MODEL_SEEDANCE_LITE_I2V_API)
        
        payload = {
            "model": model_id,
            "content": content
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/contents/generations/tasks",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.text
                except:
                    pass
            return {"error": f"Failed to create first-last frame task: {error_detail}"}
    
    def create_image_refs_task(self, 
                               ref_images: List[str] = None,  # List of image paths or URLs
                               prompt: str = "",
                               model: str = "Bytedance-Seedance-1.0-Lite-i2v",
                               resolution: str = "720p", 
                               duration: int = 5,
                               ratio: str = "16:9",
                               seed: Optional[int] = None,
                               watermark: bool = True) -> Dict[str, Any]:
        """Create image references based video task (supports 1-4 reference images)"""
        
        if not ref_images or len(ref_images) == 0:
            return {"error": "At least one reference image is required"}
        
        if len(ref_images) > 4:
            return {"error": "Maximum 4 reference images are supported"}
        
        content = []
        
        # Build prompt with parameters
        if prompt:
            full_prompt = f"{prompt} --rs {resolution} --dur {duration} --rt {ratio}"
        else:
            full_prompt = f"--rs {resolution} --dur {duration} --rt {ratio}"
        
        # Add seed parameter if provided
        if seed is not None:
            full_prompt += f" --seed {seed}"
        
        # Add watermark parameter  
        full_prompt += f" --wm {str(watermark).lower()}"
            
        content.append({
            "type": "text",
            "text": full_prompt
        })
        
        # Add reference images
        for ref_image in ref_images:
            if ref_image:  # Skip None/empty entries
                if ref_image.startswith('http'):
                    # It's a URL
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": ref_image
                        },
                        "role": "reference_image"
                    })
                else:
                    # It's a local file path
                    try:
                        base64_image = self.encode_image_to_base64(ref_image)
                        mime_type, _ = mimetypes.guess_type(ref_image)
                        if not mime_type or not mime_type.startswith('image/'):
                            mime_type = 'image/jpeg'
                        
                        data_url = f"data:{mime_type};base64,{base64_image}"
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            },
                            "role": "reference_image"
                        })
                    except Exception as e:
                        return {"error": f"Failed to encode reference image: {str(e)}"}
        
        # Get model ID - only Lite i2v model is supported for this feature
        model_id = self.models["image_refs"].get(model, MODEL_SEEDANCE_LITE_I2V_API)
        
        payload = {
            "model": model_id,
            "content": content
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/contents/generations/tasks",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.text
                except:
                    pass
            return {"error": f"Failed to create image refs task: {error_detail}"}
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Query task status"""
        try:
            response = requests.get(
                f"{self.base_url}/contents/generations/tasks/{task_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Query failed: {str(e)}"}
    
    def wait_for_task_completion(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for task completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_response = self.get_task_status(task_id)
            
            if "error" in status_response:
                return status_response
            
            status = status_response.get("status", "unknown")
            
            if status == "success":
                return status_response
            elif status == "failed":
                return {"error": "Task execution failed"}
            
            # Wait 5 seconds before querying again
            time.sleep(5)
        
        return {"error": "Task timeout"}

# Read environment variables in app.py
ARK_API_KEY = os.getenv("ARK_API_KEY")
ARK_BASE_URL = os.getenv("ARK_BASE_URL")



# Initialize client with environment variables from app.py
try:
    if not ARK_API_KEY or not ARK_BASE_URL:
        raise ValueError(f"Environment variables missing: ARK_API_KEY={'SET' if ARK_API_KEY else 'NOT SET'}, ARK_BASE_URL={ARK_BASE_URL or 'NOT SET'}")
    
    client = BytePlusVideoClient(api_key=ARK_API_KEY, base_url=ARK_BASE_URL)
    print("✅ BytePlus client initialized successfully")
except Exception as e:
    print(f"❌ Client initialization failed: {e}")
    client = None

def capture_logs_wrapper(func):
    """包装函数以捕获print输出"""
    def wrapper(*args, **kwargs):
        # 创建字符串缓冲区来捕获输出
        log_buffer = io.StringIO()
        
        try:
            # 重定向stdout和stderr到缓冲区
            with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
                result = func(*args, **kwargs)
            
            # 获取捕获的日志
            captured_logs = log_buffer.getvalue()
            
            # 如果函数返回两个值（video, status），将日志添加到status中
            if isinstance(result, tuple) and len(result) == 2:
                video, status = result
                if captured_logs:
                    enhanced_status = f"{status}\n\n🔍 DEBUG LOGS:\n{captured_logs}"
                    return video, enhanced_status
                return result
            else:
                return result
                
        except Exception as e:
            captured_logs = log_buffer.getvalue()
            error_msg = f"❌ Error: {str(e)}\n\n🔍 DEBUG LOGS:\n{captured_logs}"
            return None, error_msg
        finally:
            log_buffer.close()
    
    return wrapper



@capture_logs_wrapper
def text_to_video(prompt, model, resolution="720p", duration=5, ratio="16:9", seed=-1, watermark=True, progress=gr.Progress()):
    """Text-to-video generation function"""
    if not client:
        return None, "❌ Client not initialized, please check API configuration"
    
    if not prompt.strip():
        return None, "❌ Please enter video description text"
    
    progress(0.1, desc="Creating video generation task...")
    
    # Process seed value (-1 means random)
    seed_value = None if seed == -1 else int(seed)
    
    # Create task
    result = client.create_text_to_video_task(
        prompt=prompt,
        model=model,
        resolution=resolution,
        duration=duration,
        ratio=ratio,
        seed=seed_value,
        watermark=watermark
    )
    
    if "error" in result:
        error_message = result['error']
        if "404" in str(error_message):
            return None, """❌ 模型访问错误 (404)

🔧 解决方案：
1. 登录 BytePlus 控制台: https://console.byteplus.com/modelark
2. 在"模型广场"中找到并激活 Seedance 视频生成模型
3. 确保账户权限包含模型调用权限
4. 检查账户余额是否充足

💡 提示：视频生成是付费服务，需要先激活模型才能使用"""
        else:
            return None, f"❌ Task creation failed: {error_message}"
    
    task_id = result.get("id")
    if not task_id:
        return None, """❌ Failed to get task ID

🔧 可能的解决方案：
1. 请登录 BytePlus 控制台 (https://console.byteplus.com/modelark)
2. 在"模型广场"中激活 Seedance 视频生成模型
3. 确保账户有足够的权限和余额
4. 检查 API 密钥是否正确配置

💡 提示：视频生成模型需要单独激活才能使用"""
    
    progress(0.3, desc=f"Task created (ID: {task_id}), waiting for generation...")
    
    # Wait for task completion
    max_wait = 180  # 3 minutes timeout
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status_result = client.get_task_status(task_id)
        
        if "error" in status_result:
            return None, f"❌ Status query failed: {status_result['error']}"
        
        status = status_result.get("status", "")
        progress_val = min(0.3 + (time.time() - start_time) / max_wait * 0.6, 0.9)
        
        if status == "succeeded":
            progress(0.95, desc="Video generation completed, retrieving results...")
            
            # Get video URL - try multiple possible response formats
            video_url = None
            
            # Format 1: Check content.video_url (BytePlus API format)
            if "content" in status_result and isinstance(status_result["content"], dict):
                video_url = status_result["content"].get("video_url")
            
            # Format 2: Check data array
            if not video_url and "data" in status_result and status_result["data"]:
                for item in status_result["data"]:
                    if item.get("type") == "video_url":
                        video_url = item.get("url")
                        break
            
            # Format 3: Check direct video_url field
            if not video_url and "video_url" in status_result:
                video_url = status_result["video_url"]
            
            # Format 4: Check result field
            if not video_url and "result" in status_result:
                result = status_result["result"]
                if isinstance(result, dict):
                    video_url = result.get("video_url") or result.get("url")
                elif isinstance(result, list) and result:
                    for item in result:
                        if isinstance(item, dict) and ("video_url" in item or "url" in item):
                            video_url = item.get("video_url") or item.get("url")
                            break
            
            # Format 5: Check outputs field
            if not video_url and "outputs" in status_result:
                outputs = status_result["outputs"]
                if isinstance(outputs, list) and outputs:
                    for item in outputs:
                        if isinstance(item, dict) and ("video_url" in item or "url" in item):
                            video_url = item.get("video_url") or item.get("url")
                            break
            
            if video_url:
                progress(1.0, desc="✅ Video generation successful!")
                # 直接返回视频URL，不下载到本地
                return video_url, f"✅ Video generation successful!\nTask ID: {task_id}\nVideo URL: {video_url}"
            else:
                return None, f"❌ Generated video URL not found\nTask ID: {task_id}"
                
        elif status == "failed":
            error_msg = status_result.get("error", "Unknown error")
            return None, f"❌ Video generation failed: {error_msg}\nTask ID: {task_id}"
            
        elif status in ["queued", "running"]:
            progress(progress_val, desc=f"Generating video... (Status: {status})")
            time.sleep(3)
        else:
            return None, f"❌ Unknown status: {status}\nTask ID: {task_id}"
    
    return None, f"❌ Video generation timeout\nTask ID: {task_id}"

@capture_logs_wrapper
def image_to_video(image, prompt, model, resolution="720p", duration=5, ratio="16:9", seed=-1, watermark=True, progress=gr.Progress()):
    """Image-to-video generation function"""
    if not client:
        return None, "❌ Client not initialized, please check API configuration"
    
    if image is None:
        return None, "❌ Please upload an image"
    
    progress(0.1, desc="Processing uploaded image...")
    
    # Save uploaded image to temporary file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            if isinstance(image, str):
                # If it's a file path
                image_path = image
            else:
                # If it's a PIL Image object
                image.save(tmp_file.name, format="JPEG")
                image_path = tmp_file.name
        
        progress(0.2, desc="Creating image-to-video task...")
        
        # Process seed value (-1 means random)
        seed_value = None if seed == -1 else int(seed)
        
        # Create task using the actual uploaded image
        result = client.create_image_to_video_task(
            image_path=image_path,
            prompt=prompt,
            model=model,
            resolution=resolution,
            duration=duration,
            ratio=ratio,
            seed=seed_value,
            watermark=watermark
        )
        
        if "error" in result:
            error_message = result['error']
            if "404" in str(error_message):
                return None, """❌ 模型访问错误 (404)

🔧 解决方案：
1. 登录 BytePlus 控制台: https://console.byteplus.com/modelark
2. 在"模型广场"中找到并激活 Seedance 视频生成模型
3. 确保账户权限包含模型调用权限
4. 检查账户余额是否充足

💡 提示：视频生成是付费服务，需要先激活模型才能使用"""
            else:
                return None, f"❌ Task creation failed: {error_message}"
        
        task_id = result.get("id")
        if not task_id:
            return None, """❌ Failed to get task ID

🔧 可能的解决方案：
1. 请登录 BytePlus 控制台 (https://console.byteplus.com/modelark)
2. 在"模型广场"中激活 Seedance 视频生成模型
3. 确保账户有足够的权限和余额
4. 检查 API 密钥是否正确配置

💡 提示：视频生成模型需要单独激活才能使用"""
        
        progress(0.3, desc=f"Task created (ID: {task_id}), waiting for generation...")
        
        # Wait for task completion
        max_wait = 180  # 3 minutes timeout
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_result = client.get_task_status(task_id)
            
            if "error" in status_result:
                return None, f"❌ Status query failed: {status_result['error']}"
            
            status = status_result.get("status", "")
            progress_val = min(0.3 + (time.time() - start_time) / max_wait * 0.6, 0.9)
            
            if status == "succeeded":
                progress(0.95, desc="Video generation completed, retrieving results...")
                
                # Get video URL - try multiple possible response formats
                video_url = None
                
                # Format 1: Check content.video_url (BytePlus API format)
                if "content" in status_result and isinstance(status_result["content"], dict):
                    video_url = status_result["content"].get("video_url")
                
                # Format 2: Check data array
                if not video_url and "data" in status_result and status_result["data"]:
                    for item in status_result["data"]:
                        if item.get("type") == "video_url":
                            video_url = item.get("url")
                            break
                
                # Format 3: Check direct video_url field
                if not video_url and "video_url" in status_result:
                    video_url = status_result["video_url"]
                
                # Format 4: Check result field
                if not video_url and "result" in status_result:
                    result = status_result["result"]
                    if isinstance(result, dict):
                        video_url = result.get("video_url") or result.get("url")
                    elif isinstance(result, list) and result:
                        for item in result:
                            if isinstance(item, dict) and ("video_url" in item or "url" in item):
                                video_url = item.get("video_url") or item.get("url")
                                break
                
                # Format 5: Check outputs field
                if not video_url and "outputs" in status_result:
                    outputs = status_result["outputs"]
                    if isinstance(outputs, list) and outputs:
                        for item in outputs:
                            if isinstance(item, dict) and ("video_url" in item or "url" in item):
                                video_url = item.get("video_url") or item.get("url")
                                break
                
                if video_url:
                    progress(1.0, desc="✅ Video generation successful!")
                    # 直接返回视频URL，不下载到本地
                    return video_url, f"✅ Video generation successful!\nTask ID: {task_id}\nVideo URL: {video_url}"
                else:
                    return None, f"❌ Generated video URL not found\nTask ID: {task_id}"
                    
            elif status == "failed":
                error_msg = status_result.get("error", "Unknown error")
                return None, f"❌ Video generation failed: {error_msg}\nTask ID: {task_id}"
                
            elif status in ["queued", "running"]:
                progress(progress_val, desc=f"Generating video... (Status: {status})")
                time.sleep(3)
            else:
                return None, f"❌ Unknown status: {status}\nTask ID: {task_id}"
        
        return None, f"❌ Video generation timeout\nTask ID: {task_id}"
        
    except Exception as e:
        return None, f"❌ Error processing image: {str(e)}"
    finally:
        # Clean up temporary files
        if 'image_path' in locals() and os.path.exists(image_path):
            try:
                os.unlink(image_path)
            except:
                pass

@capture_logs_wrapper
def first_last_frame_to_video(first_frame, last_frame, prompt, resolution="720p", duration=5, cf=False, seed=-1, watermark=True, progress=gr.Progress()):
    """First-last frame to video generation function"""
    if not client:
        return None, "❌ Client not initialized, please check API configuration"
    
    if first_frame is None or last_frame is None:
        return None, "❌ Please upload both first frame and last frame images"
    
    progress(0.1, desc="Processing uploaded images...")
    
    # Save uploaded images to temporary files
    try:
        # Process first frame
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            if isinstance(first_frame, str):
                first_frame_path = first_frame
            else:
                first_frame.save(tmp_file.name, format="JPEG")
                first_frame_path = tmp_file.name
        
        # Process last frame
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            if isinstance(last_frame, str):
                last_frame_path = last_frame
            else:
                last_frame.save(tmp_file.name, format="JPEG")
                last_frame_path = tmp_file.name
        
        progress(0.2, desc="Creating first-last frame video task...")
        
        # Process seed value (-1 means random)
        seed_value = None if seed == -1 else int(seed)
        
        # Create task - only supports Bytedance-Seedance-1.0-Lite-i2v model
        result = client.create_first_last_frame_task(
            first_frame_path=first_frame_path,
            last_frame_path=last_frame_path,
            prompt=prompt,
            model="Bytedance-Seedance-1.0-Lite-i2v",  # Only this model is supported
            resolution=resolution,
            duration=duration,
            cf=cf,
            seed=seed_value,
            watermark=watermark
        )
        
        if "error" in result:
            error_message = result['error']
            if "404" in str(error_message):
                return None, """❌ 模型访问错误 (404)

🔧 解决方案：
1. 登录 BytePlus 控制台: https://console.byteplus.com/modelark
2. 在"模型广场"中找到并激活 Seedance 视频生成模型
3. 确保账户权限包含模型调用权限
4. 检查账户余额是否充足

💡 提示：视频生成是付费服务，需要先激活模型才能使用"""
            else:
                return None, f"❌ Task creation failed: {error_message}"
        
        task_id = result.get("id")
        if not task_id:
            return None, """❌ Failed to get task ID

🔧 可能的解决方案：
1. 请登录 BytePlus 控制台 (https://console.byteplus.com/modelark)
2. 在"模型广场"中激活 Seedance 视频生成模型
3. 确保账户有足够的权限和余额
4. 检查 API 密钥是否正确配置

💡 提示：视频生成模型需要单独激活才能使用"""
        
        progress(0.3, desc=f"Task created (ID: {task_id}), waiting for generation...")
        
        # Wait for task completion
        max_wait = 180  # 3 minutes timeout
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_result = client.get_task_status(task_id)
            
            if "error" in status_result:
                return None, f"❌ Status query failed: {status_result['error']}"
            
            status = status_result.get("status", "")
            progress_val = min(0.3 + (time.time() - start_time) / max_wait * 0.6, 0.9)
            
            if status == "succeeded":
                progress(0.95, desc="Video generation completed, retrieving results...")
                
                # Get video URL - try multiple possible response formats
                video_url = None
                
                # Format 1: Check content.video_url (BytePlus API format)
                if "content" in status_result and isinstance(status_result["content"], dict):
                    video_url = status_result["content"].get("video_url")
                
                # Format 2: Check data array
                if not video_url and "data" in status_result and status_result["data"]:
                    for item in status_result["data"]:
                        if item.get("type") == "video_url":
                            video_url = item.get("url")
                            break
                
                # Format 3: Check direct video_url field
                if not video_url and "video_url" in status_result:
                    video_url = status_result["video_url"]
                
                # Format 4: Check result field
                if not video_url and "result" in status_result:
                    result = status_result["result"]
                    if isinstance(result, dict):
                        video_url = result.get("video_url") or result.get("url")
                    elif isinstance(result, list) and result:
                        for item in result:
                            if isinstance(item, dict) and ("video_url" in item or "url" in item):
                                video_url = item.get("video_url") or item.get("url")
                                break
                
                # Format 5: Check outputs field
                if not video_url and "outputs" in status_result:
                    outputs = status_result["outputs"]
                    if isinstance(outputs, list) and outputs:
                        for item in outputs:
                            if isinstance(item, dict) and ("video_url" in item or "url" in item):
                                video_url = item.get("video_url") or item.get("url")
                                break
                
                if video_url:
                    progress(1.0, desc="✅ Video generation successful!")
                    return video_url, f"✅ Video generation successful!\nTask ID: {task_id}\nVideo URL: {video_url}"
                else:
                    return None, f"❌ Generated video URL not found\nTask ID: {task_id}"
                    
            elif status == "failed":
                error_msg = status_result.get("error", "Unknown error")
                return None, f"❌ Video generation failed: {error_msg}\nTask ID: {task_id}"
                
            elif status in ["queued", "running"]:
                progress(progress_val, desc=f"Generating video... (Status: {status})")
                time.sleep(3)
            else:
                return None, f"❌ Unknown status: {status}\nTask ID: {task_id}"
        
        return None, f"❌ Video generation timeout\nTask ID: {task_id}"
        
    except Exception as e:
        return None, f"❌ Error processing images: {str(e)}"
    finally:
        # Clean up temporary files
        if 'first_frame_path' in locals() and os.path.exists(first_frame_path):
            try:
                os.unlink(first_frame_path)
            except:
                pass
        if 'last_frame_path' in locals() and os.path.exists(last_frame_path):
            try:
                os.unlink(last_frame_path)
            except:
                pass

@capture_logs_wrapper
def image_refs_to_video(ref_image1, ref_image2, ref_image3, ref_image4, prompt, resolution="720p", duration=5, ratio="16:9", seed=-1, watermark=True, progress=gr.Progress()):
    """Image references to video generation function"""
    if not client:
        return None, "❌ Client not initialized, please check API configuration"
    
    # Collect non-None reference images
    ref_images_paths = []
    ref_images = [ref_image1, ref_image2, ref_image3, ref_image4]
    
    for img in ref_images:
        if img is not None:
            ref_images_paths.append(img)
    
    if len(ref_images_paths) == 0:
        return None, "❌ Please upload at least one reference image"
    
    progress(0.1, desc=f"Processing {len(ref_images_paths)} reference images...")
    
    # Save uploaded images to temporary files
    temp_files = []
    try:
        processed_images = []
        for i, image in enumerate(ref_images_paths):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                if isinstance(image, str):
                    # If it's a file path
                    image_path = image
                else:
                    # If it's a PIL Image object
                    image.save(tmp_file.name, format="JPEG")
                    image_path = tmp_file.name
                processed_images.append(image_path)
                temp_files.append(image_path)
        
        progress(0.2, desc="Creating image refs video task...")
        
        # Process seed value (-1 means random)
        seed_value = None if seed == -1 else int(seed)
        
        # Create task - only supports Bytedance-Seedance-1.0-Lite-i2v model
        result = client.create_image_refs_task(
            ref_images=processed_images,
            prompt=prompt,
            model="Bytedance-Seedance-1.0-Lite-i2v",  # Only this model is supported
            resolution=resolution,
            duration=duration,
            ratio=ratio,
            seed=seed_value,
            watermark=watermark
        )
        
        if "error" in result:
            error_message = result['error']
            if "404" in str(error_message):
                return None, """❌ 模型访问错误 (404)

🔧 解决方案：
1. 登录 BytePlus 控制台: https://console.byteplus.com/modelark
2. 在"模型广场"中找到并激活 Seedance 视频生成模型
3. 确保账户权限包含模型调用权限
4. 检查账户余额是否充足

💡 提示：视频生成是付费服务，需要先激活模型才能使用"""
            else:
                return None, f"❌ Task creation failed: {error_message}"
        
        task_id = result.get("id")
        if not task_id:
            return None, """❌ Failed to get task ID

🔧 可能的解决方案：
1. 请登录 BytePlus 控制台 (https://console.byteplus.com/modelark)
2. 在"模型广场"中激活 Seedance 视频生成模型
3. 确保账户有足够的权限和余额
4. 检查 API 密钥是否正确配置

💡 提示：视频生成模型需要单独激活才能使用"""
        
        progress(0.3, desc=f"Task created (ID: {task_id}), waiting for generation...")
        
        # Wait for task completion
        max_wait = 180  # 3 minutes timeout
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_result = client.get_task_status(task_id)
            
            if "error" in status_result:
                return None, f"❌ Status query failed: {status_result['error']}"
            
            status = status_result.get("status", "")
            progress_val = min(0.3 + (time.time() - start_time) / max_wait * 0.6, 0.9)
            
            if status == "succeeded":
                progress(0.95, desc="Video generation completed, retrieving results...")
                
                # Get video URL - try multiple possible response formats
                video_url = None
                
                # Format 1: Check content.video_url (BytePlus API format)
                if "content" in status_result and isinstance(status_result["content"], dict):
                    video_url = status_result["content"].get("video_url")
                
                # Format 2: Check data array
                if not video_url and "data" in status_result and status_result["data"]:
                    for item in status_result["data"]:
                        if item.get("type") == "video_url":
                            video_url = item.get("url")
                            break
                
                # Format 3: Check direct video_url field
                if not video_url and "video_url" in status_result:
                    video_url = status_result["video_url"]
                
                # Format 4: Check result field
                if not video_url and "result" in status_result:
                    result = status_result["result"]
                    if isinstance(result, dict):
                        video_url = result.get("video_url") or result.get("url")
                    elif isinstance(result, list) and result:
                        for item in result:
                            if isinstance(item, dict) and ("video_url" in item or "url" in item):
                                video_url = item.get("video_url") or item.get("url")
                                break
                
                # Format 5: Check outputs field
                if not video_url and "outputs" in status_result:
                    outputs = status_result["outputs"]
                    if isinstance(outputs, list) and outputs:
                        for item in outputs:
                            if isinstance(item, dict) and ("video_url" in item or "url" in item):
                                video_url = item.get("video_url") or item.get("url")
                                break
                
                if video_url:
                    progress(1.0, desc="✅ Video generation successful!")
                    return video_url, f"✅ Video generation successful with {len(ref_images_paths)} reference images!\nTask ID: {task_id}\nVideo URL: {video_url}"
                else:
                    return None, f"❌ Generated video URL not found\nTask ID: {task_id}"
                    
            elif status == "failed":
                error_msg = status_result.get("error", "Unknown error")
                return None, f"❌ Video generation failed: {error_msg}\nTask ID: {task_id}"
                
            elif status in ["queued", "running"]:
                progress(progress_val, desc=f"Generating video... (Status: {status})")
                time.sleep(3)
            else:
                return None, f"❌ Unknown status: {status}\nTask ID: {task_id}"
        
        return None, f"❌ Video generation timeout\nTask ID: {task_id}"
        
    except Exception as e:
        return None, f"❌ Error processing images: {str(e)}"
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass

def create_demo():
    """Create Gradio demo interface"""
    
    # Custom CSS styles
    css = """
    .gradio-container {
        max-width: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 20px !important;
    }
    @media (min-width: 768px) {
        .gradio-container {
            padding: 0 40px !important;
        }
    }
    @media (min-width: 1200px) {
        .gradio-container {
            padding: 0 60px !important;
        }
    }
    .tab-nav {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    }
    .tab-nav button {
        color: white !important;
        font-weight: bold !important;
    }
    .tab-nav button.selected {
        background: rgba(255,255,255,0.2) !important;
    }
    h1 {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5em;
        margin-bottom: 1em;
    }
    .info-box {
        background: #f0f8ff;
        border: 1px solid #b0d4f1;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .gradio-group {
        background: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .input-section {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .output-section {
        background: linear-gradient(135deg, #e8f5e8 0%, #d4e7d4 100%);
    }
    """
    
    with gr.Blocks(css=css, title="BytePlus Video Generation Tool") as demo:
        gr.HTML(f"""
        <h1>🎬 BytePlus ModelArk Video Generation</h1>
        <div class="info-box">
            <p><strong>🚀 Features:</strong></p>
            <ul>
                <li><strong>Text-to-Video:</strong> Generate videos from text descriptions</li>
                <li><strong>Image-to-Video:</strong> Generate videos from images with action descriptions</li>
                <li><strong>Image-with-FirstLastFrame:</strong> Generate transition videos between two frames (Lite-i2v model only)</li>
                <li><strong>Image-Refs:</strong> Generate videos using 1-4 reference images (Lite-i2v model only)</li>
            </ul>
            <p><strong>🔧 Model:</strong>Bytedance-Seedance-1.0-pro and ByteDance Seedance-1.0-lite (Efficient Version)</p>
        </div>
        """)
        
        with gr.Tabs():
            # Text-to-video tab
            with gr.TabItem("📝 Text-to-Video", id="text_to_video"):
                with gr.Row():
                    # Left Side - Input Section
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes=["input-section"]):
                            gr.HTML("<h3>📝 Text Description</h3>")
                            t2v_prompt = gr.Textbox(
                                label="Video Description",
                                placeholder="Please describe in detail the video content you want to generate, e.g.: A cute cat playing in a garden, bright sunlight, slow camera push...",
                                lines=6,
                                max_lines=15,
                                max_length=5000
                            )
                            
                            gr.HTML("<h3>🤖 Model Selection</h3>")
                            t2v_model = gr.Dropdown(
                                choices=["Bytedance-Seedance-1.0-pro", "Bytedance-Seedance-1.0-Lite-t2v"],
                                value="Bytedance-Seedance-1.0-Lite-t2v",
                                label="Model"
                            )
                            
                            gr.HTML("<h3>⚙️ Generation Parameters</h3>")
                            t2v_resolution = gr.Dropdown(
                                choices=["480p", "720p", "1080p"],
                                value="720p",
                                label="Resolution"
                            )
                            with gr.Row():
                                t2v_duration = gr.Slider(
                                    minimum=3,
                                    maximum=12,
                                    value=5,
                                    step=1,
                                    label="Duration (seconds)"
                                )
                                t2v_ratio = gr.Dropdown(
                                    choices=["16:9", "4:3", "1:1", "3:4", "9:16"],
                                    value="16:9",
                                    label="Aspect Ratio"
                                )
                            
                            with gr.Row():
                                t2v_seed = gr.Number(
                                    value=-1,
                                    label="Seed",
                                    info="Range: [-1, 4294967295]. Use -1 for random, or specify a value for reproducible results",
                                    minimum=-1,
                                    maximum=4294967295,
                                    step=1,
                                    precision=0
                                )
                                t2v_watermark = gr.Checkbox(
                                    value=True,
                                    label="Add Watermark",
                                    info="Include BytePlus watermark in the video"
                                )
                            
                            t2v_generate_btn = gr.Button("🎬 Generate Video", variant="primary", size="lg")
                    
                    # Right Side - Output Section
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes=["output-section"]):
                            gr.HTML("<h3>🎥 Generation Result</h3>")
                            t2v_video_output = gr.Video(label="Generated Video", height=400)
                            t2v_status_output = gr.Textbox(
                                label="Status Information & Debug Logs",
                                lines=12,
                                max_lines=20,
                                interactive=False,
                                visible=True
                            )
                
                # Example tips
                gr.HTML("""
                <div class="info-box">
                    <p><strong>💡 Prompt Suggestions:</strong></p>
                    <ul>
                        <li>Describe scenes, actions, lighting, and camera movements in detail</li>
                        <li>Can include emotional tone and artistic style</li>
                        <li>Supports both English and Chinese descriptions</li>
                    </ul>
                </div>
                """)
            
            # Image-to-video tab
            with gr.TabItem("🖼️ Image-to-Video", id="image_to_video"):
                with gr.Row():
                    # Left Side - Input Section
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes=["input-section"]):
                            gr.HTML("<h3>🖼️ Upload Image</h3>")
                            i2v_image_input = gr.Image(
                                label="Select Image",
                                type="pil",
                                height=250,
                                sources=["upload"]
                            )
                            
                            gr.HTML("<h3>📝 Action Description</h3>")
                            i2v_prompt = gr.Textbox(
                                label="Video Description",
                                placeholder="Optional: Describe how you want the image to animate, e.g.: Person smiling and waving, leaves in the background gently swaying...",
                                lines=4,
                                max_lines=10,
                                max_length=5000
                            )
                            
                            gr.HTML("<h3>🤖 Model Selection</h3>")
                            i2v_model = gr.Dropdown(
                                choices=["Bytedance-Seedance-1.0-pro", "Bytedance-Seedance-1.0-Lite-i2v"],
                                value="Bytedance-Seedance-1.0-Lite-i2v",
                                label="Model"
                            )
                            
                            gr.HTML("<h3>⚙️ Generation Parameters</h3>")
                            i2v_resolution = gr.Dropdown(
                                choices=["480p", "720p", "1080p"],
                                value="720p",
                                label="Resolution"
                            )
                            with gr.Row():
                                i2v_duration = gr.Slider(
                                    minimum=3,
                                    maximum=12,
                                    value=5,
                                    step=1,
                                    label="Duration (seconds)"
                                )
                                i2v_ratio = gr.Dropdown(
                                    choices=["adaptive", "16:9", "4:3", "1:1", "3:4", "9:16"],
                                    value="adaptive",
                                    label="Aspect Ratio"
                                )
                            
                            with gr.Row():
                                i2v_seed = gr.Number(
                                    value=-1,
                                    label="Seed",
                                    info="Range: [-1, 4294967295]. Use -1 for random, or specify a value for reproducible results",
                                    minimum=-1,
                                    maximum=4294967295,
                                    step=1,
                                    precision=0
                                )
                                i2v_watermark = gr.Checkbox(
                                    value=True,
                                    label="Add Watermark",
                                    info="Include BytePlus watermark in the video"
                                )
                            
                            i2v_generate_btn = gr.Button("🎬 Generate Video", variant="primary", size="lg")
                    
                    # Right Side - Output Section
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes=["output-section"]):
                            gr.HTML("<h3>🎥 Generation Result</h3>")
                            i2v_video_output = gr.Video(label="Generated Video", height=400)
                            i2v_status_output = gr.Textbox(
                                label="Status Information & Debug Logs",
                                lines=12,
                                max_lines=20,
                                interactive=False,
                                visible=True
                            )
                
                # Example tips
                gr.HTML("""
                <div class="info-box">
                    <p><strong>💡 Image-to-Video Suggestions:</strong></p>
                    <ul>
                        <li>Upload clear, well-composed images (minimum width: 300px)</li>
                        <li>Text description is optional; the system will automatically analyze the image</li>
                        <li>Recommend using "adaptive" aspect ratio to match image proportions</li>
                    </ul>
                </div>
                """)
            
            # First-Last Frame to Video tab
            with gr.TabItem("🎞️ Image-with-FirstLastFrame", id="first_last_frame"):
                with gr.Row():
                    # Left Side - Input Section
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes=["input-section"]):
                            gr.HTML("<h3>🎬 First Frame & Last Frame</h3>")
                            gr.HTML("<p style='color: #666; margin-bottom: 15px;'>This feature only supports <strong>Bytedance-Seedance-1.0-Lite-i2v</strong> model</p>")
                            
                            flf_first_frame = gr.Image(
                                label="First Frame",
                                type="pil",
                                height=200,
                                sources=["upload"]
                            )
                            
                            flf_last_frame = gr.Image(
                                label="Last Frame",
                                type="pil",
                                height=200,
                                sources=["upload"]
                            )
                            
                            gr.HTML("<h3>📝 Action Description</h3>")
                            flf_prompt = gr.Textbox(
                                label="Video Description",
                                placeholder="Optional: Describe the transformation or motion between frames, e.g.: A blue-green jingwei bird transforms into a human form...",
                                lines=4,
                                max_lines=10,
                                max_length=5000
                            )
                            
                            gr.HTML("<h3>⚙️ Generation Parameters</h3>")
                            flf_resolution = gr.Dropdown(
                                choices=["480p", "720p", "1080p"],
                                value="720p",
                                label="Resolution (--rs parameter)"
                            )
                            with gr.Row():
                                flf_duration = gr.Slider(
                                    minimum=3,
                                    maximum=12,
                                    value=5,
                                    step=1,
                                    label="Duration in seconds (--dur parameter)"
                                )
                                flf_cf = gr.Checkbox(
                                    value=False,
                                    label="Content Fill Mode (--cf parameter)",
                                    info="Enable content fill mode for smoother transitions"
                                )
                            
                            with gr.Row():
                                flf_seed = gr.Number(
                                    value=-1,
                                    label="Seed",
                                    info="Range: [-1, 4294967295]. Use -1 for random",
                                    minimum=-1,
                                    maximum=4294967295,
                                    step=1,
                                    precision=0
                                )
                                flf_watermark = gr.Checkbox(
                                    value=True,
                                    label="Add Watermark",
                                    info="Include BytePlus watermark in the video"
                                )
                            
                            flf_generate_btn = gr.Button("🎬 Generate Video", variant="primary", size="lg")
                    
                    # Right Side - Output Section
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes=["output-section"]):
                            gr.HTML("<h3>🎥 Generation Result</h3>")
                            flf_video_output = gr.Video(label="Generated Video", height=400)
                            flf_status_output = gr.Textbox(
                                label="Status Information & Debug Logs",
                                lines=12,
                                max_lines=20,
                                interactive=False,
                                visible=True
                            )
                
                # Example tips
                gr.HTML("""
                <div class="info-box">
                    <p><strong>💡 First-Last Frame Video Tips:</strong></p>
                    <ul>
                        <li>Upload both first frame and last frame images (required)</li>
                        <li>The model will generate smooth transitions between the two frames</li>
                        <li>Text description helps guide the transformation style</li>
                        <li>Only supports <strong>Bytedance-Seedance-1.0-Lite-i2v</strong> model</li>
                    </ul>
                </div>
                """)
            
            # Image References to Video tab
            with gr.TabItem("🖼️ Image-Refs", id="image_refs"):
                with gr.Row():
                    # Left Side - Input Section
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes=["input-section"]):
                            gr.HTML("<h3>🖼️ Reference Images (1-4)</h3>")
                            gr.HTML("<p style='color: #666; margin-bottom: 15px;'>Upload 1-4 reference images. This feature only supports <strong>Bytedance-Seedance-1.0-Lite-i2v</strong> model</p>")
                            
                            with gr.Row():
                                ref_image1 = gr.Image(
                                    label="Reference Image 1",
                                    type="pil",
                                    height=150,
                                    sources=["upload"]
                                )
                                ref_image2 = gr.Image(
                                    label="Reference Image 2",
                                    type="pil",
                                    height=150,
                                    sources=["upload"]
                                )
                            
                            with gr.Row():
                                ref_image3 = gr.Image(
                                    label="Reference Image 3",
                                    type="pil",
                                    height=150,
                                    sources=["upload"]
                                )
                                ref_image4 = gr.Image(
                                    label="Reference Image 4",
                                    type="pil",
                                    height=150,
                                    sources=["upload"]
                                )
                            
                            gr.HTML("<h3>📝 Video Description</h3>")
                            ref_prompt = gr.Textbox(
                                label="Video Description",
                                placeholder="Describe the video content, e.g.: The old man is in a cafe, holding a coffee cup, the picture style is cartoon and fresh...",
                                lines=4,
                                max_lines=10,
                                max_length=5000
                            )
                            
                            gr.HTML("<h3>⚙️ Generation Parameters</h3>")
                            ref_resolution = gr.Dropdown(
                                choices=["480p", "720p", "1080p"],
                                value="720p",
                                label="Resolution (--rs parameter)"
                            )
                            with gr.Row():
                                ref_duration = gr.Slider(
                                    minimum=3,
                                    maximum=12,
                                    value=5,
                                    step=1,
                                    label="Duration in seconds (--dur parameter)"
                                )
                                ref_ratio = gr.Dropdown(
                                    choices=["16:9", "4:3", "1:1", "3:4", "9:16"],
                                    value="16:9",
                                    label="Aspect Ratio (--rt parameter)"
                                )
                            
                            with gr.Row():
                                ref_seed = gr.Number(
                                    value=-1,
                                    label="Seed",
                                    info="Range: [-1, 4294967295]. Use -1 for random",
                                    minimum=-1,
                                    maximum=4294967295,
                                    step=1,
                                    precision=0
                                )
                                ref_watermark = gr.Checkbox(
                                    value=True,
                                    label="Add Watermark (--wm parameter)",
                                    info="Include BytePlus watermark in the video"
                                )
                            
                            ref_generate_btn = gr.Button("🎬 Generate Video", variant="primary", size="lg")
                    
                    # Right Side - Output Section
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes=["output-section"]):
                            gr.HTML("<h3>🎥 Generation Result</h3>")
                            ref_video_output = gr.Video(label="Generated Video", height=400)
                            ref_status_output = gr.Textbox(
                                label="Status Information & Debug Logs",
                                lines=12,
                                max_lines=20,
                                interactive=False,
                                visible=True
                            )
                
                # Example tips
                gr.HTML("""
                <div class="info-box">
                    <p><strong>💡 Reference Images Video Tips:</strong></p>
                    <ul>
                        <li>Upload 1-4 reference images to guide the video generation</li>
                        <li>The model uses these images as style and content references</li>
                        <li>More reference images provide better guidance for the generated video</li>
                        <li>Only supports <strong>Bytedance-Seedance-1.0-Lite-i2v</strong> model</li>
                    </ul>
                </div>
                """)
        
        # Bind events
        t2v_generate_btn.click(
            fn=text_to_video,
            inputs=[t2v_prompt, t2v_model, t2v_resolution, t2v_duration, t2v_ratio, t2v_seed, t2v_watermark],
            outputs=[t2v_video_output, t2v_status_output]
        )
        
        i2v_generate_btn.click(
            fn=image_to_video,
            inputs=[i2v_image_input, i2v_prompt, i2v_model, i2v_resolution, i2v_duration, i2v_ratio, i2v_seed, i2v_watermark],
            outputs=[i2v_video_output, i2v_status_output]
        )
        
        flf_generate_btn.click(
            fn=first_last_frame_to_video,
            inputs=[flf_first_frame, flf_last_frame, flf_prompt, flf_resolution, flf_duration, flf_cf, flf_seed, flf_watermark],
            outputs=[flf_video_output, flf_status_output]
        )
        
        ref_generate_btn.click(
            fn=image_refs_to_video,
            inputs=[ref_image1, ref_image2, ref_image3, ref_image4, ref_prompt, ref_resolution, ref_duration, ref_ratio, ref_seed, ref_watermark],
            outputs=[ref_video_output, ref_status_output]
        )
        
        # Footer information
        gr.HTML("""
        <div style="text-align: center; margin-top: 2em; padding: 1em; border-top: 1px solid #eee;">
            <p>🔧 <strong>Tech Stack:</strong> BytePlus ModelArk + Gradio</p>
            <p>🤖 <strong>Model:</strong> ByteDance Seedance-1.0-lite</p>
            <p>⚡ <strong>Features:</strong> Efficient, Fast, High-Quality Video Generation</p>
        </div>
        """)
    
    return demo

if __name__ == "__main__":
    # Create and launch demo
    demo = create_demo()
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)