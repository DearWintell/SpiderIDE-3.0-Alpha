import subprocess
import sys
import os
import threading


class Runner:
    
    process = None
    _stop_requested = False
    _running_lock = threading.Lock()
    debug_file = None
    
    @classmethod
    def run(cls, file_path, console, debug=False):
        with cls._running_lock:
            if cls.process and cls.process.poll() is None:
                cls._force_stop()
            
            cls._stop_requested = False
        
        if debug:
            cls.debug_file = os.path.join(os.path.dirname(file_path), '.spider_debug.json')
            if os.path.exists(cls.debug_file):
                try:
                    os.remove(cls.debug_file)
                except Exception:
                    pass
        else:
            cls.debug_file = None
        
        console.clear()
        mode = "DEBUG" if debug else "RUN"
        console.write(f"▶ [{mode}] Running: {file_path}\n", 'success')
        console.write(f"{'='*50}\n\n", 'info')
        
        def run_thread():
            try:
                spider_path = cls._find_spider_runtime()
                
                if not spider_path:
                    console.write("spider.py not found!\n", 'error')
                    return
                
                console.write(f"✓ Found: {spider_path}\n\n", 'success')
                
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONUNBUFFERED'] = '1'
                
                if cls.debug_file:
                    env['SPIDER_DEBUG_FILE'] = cls.debug_file
                
                creation_flags = 0x08000000 
                

                if spider_path.endswith('.exe'):

                    cmd = [spider_path, file_path]
                else:

                    cmd = [sys.executable, '-u', spider_path, file_path]
                

                cls.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1,
                    cwd=os.path.dirname(file_path) or '.',
                    env=env,
                    creationflags=creation_flags
                )
                

                for line in cls.process.stdout:
                    if cls._stop_requested:
                        break
                    
                    if line:
                        line_lower = line.lower()
                        
                        if any(err in line_lower for err in ['error', 'traceback', 'exception', '[error]']):
                            console.write(line, 'error')
                        elif any(succ in line_lower for succ in ['success', 'done', 'finished', 'created']):
                            console.write(line, 'success')
                        elif any(warn in line_lower for warn in ['warning', 'warn', '[warning]']):
                            console.write(line, 'warning')
                        else:
                            console.write(line)
                

                cls.process.wait()
                
                if cls._stop_requested:
                    console.write(f"\n Process stopped by user\n", 'warning')
                elif cls.process.returncode == 0:
                    console.write(f"\n Execution finished\n", 'success')
                else:
                    console.write(f"\n Execution failed (code: {cls.process.returncode})\n", 'error')
                    
            except Exception as e:
                console.write(f"\n Error: {str(e)}\n", 'error')
            finally:
                with cls._running_lock:
                    cls.process = None
                    cls._stop_requested = False
                
        thread = threading.Thread(target=run_thread, daemon=True)
        thread.start()
    
    @classmethod
    def _find_spider_runtime(cls):

        if hasattr(sys, '_MEIPASS'):
            exe_path = os.path.join(sys._MEIPASS, 'spider_runtime', 'spider.py')
            if os.path.exists(exe_path):
                return exe_path
            

            base_dir = os.path.dirname(sys.executable)
            runtime_exe = os.path.join(base_dir, 'spider_runtime.exe')
            if os.path.exists(runtime_exe):
                return runtime_exe
        

        base_dir = os.path.dirname(os.path.abspath(__file__))
        paths_to_try = [
            os.path.join(base_dir, '..', '..', 'spider_runtime', 'spider.py'),
            os.path.join(base_dir, '..', '..', '..', 'spider_runtime', 'spider.py'),
            os.path.join(os.path.dirname(base_dir), 'spider_runtime', 'spider.py'),
        ]
        
        for p in paths_to_try:
            normalized = os.path.normpath(p)
            if os.path.exists(normalized):
                return normalized
        
        return None
    
    @classmethod
    def stop(cls):
        cls._stop_requested = True
        
        if cls.process:
            try:
                cls.process.terminate()
                try:
                    cls.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    cls.process.kill()
                    cls.process.wait()
            except Exception:
                pass
            finally:
                with cls._running_lock:
                    cls.process = None
    
    @classmethod
    def _force_stop(cls):

        cls._stop_requested = True
        if cls.process:
            try:
                cls.process.kill()
                cls.process.wait(timeout=2)
            except Exception:
                pass
            finally:
                cls.process = None
    
    @classmethod
    def is_running(cls):

        with cls._running_lock:
            return cls.process is not None and cls.process.poll() is None 