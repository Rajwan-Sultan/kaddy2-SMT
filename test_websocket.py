import asyncio
import websockets
import json
import sys
import os

async def send_file_for_analysis(websocket, file_path):
    """Send a single file for analysis and return the result."""
    try:
        with open(file_path, "rb") as audio_file:
            print(f"\n{'='*60}")
            print(f"Streaming file: {os.path.basename(file_path)}")
            print(f"{'='*60}")
            
            # Read entire file and send
            audio_data = audio_file.read()
            bytes_sent = len(audio_data)
            
            print(f"Sending {bytes_sent} bytes...")
            await websocket.send(audio_data)
            print(f"✓ File sent ({bytes_sent} bytes)")
            
            # Trigger analysis immediately
            print("Triggering analysis...")
            await websocket.send("ANALYZE")
            
            # Receive processing status
            status_msg = await websocket.recv()
            status_data = json.loads(status_msg)
            print(f"Status: {status_data['status']} - {status_data.get('audio_size_bytes', 0)} bytes")
            
            # Receive analysis result
            result_msg = await websocket.recv()
            result_data = json.loads(result_msg)
            
            if result_data['status'] == 'complete':
                print(f"\n{'='*60}")
                print("✓ ANALYSIS COMPLETE")
                print(f"{'='*60}")
                analysis = result_data['analysis']
                print(f"Scam Detected: {analysis['scam_detected']}")
                print(f"Confidence Score: {analysis['confidence_score']}%")
                print(f"Explanation: {analysis['explanation']}")
                if analysis.get('scam_tags'):
                    print(f"Scam Tags: {', '.join([tag['tag'] for tag in analysis['scam_tags']])}")
                if analysis.get('risk_factors'):
                    print(f"\nRisk Factors:")
                    for factor, score in analysis['risk_factors'].items():
                        if score:
                            print(f"  - {factor}: {score}/10")
                print(f"{'='*60}")
                
                return True
            elif result_data['status'] == 'error':
                print(f"✗ Error: {result_data['error']}")
                return False
                
    except FileNotFoundError:
        print(f"✗ Error: File not found: {file_path}")
        return False
    except Exception as e:
        print(f"✗ Error processing file: {e}")
        return False

async def test_websocket():
    """Test the WebSocket audio streaming endpoint with multiple files."""
    uri = "ws://127.0.0.1:8000/analyzer_audio_stream"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            # Step 1: Receive connection confirmation
            response = await websocket.recv()
            print(f"✓ Connected: {response}\n")
            
            # Step 2: Get first audio file and detect format
            audio_file_path = input("Enter the path to your first audio file: ").strip()
            
            if not audio_file_path:
                print("⚠ No file provided. Exiting...")
                return
            
            if not os.path.exists(audio_file_path):
                print(f"✗ Error: File not found: {audio_file_path}")
                return
            
            # Automatically detect audio format from file extension
            file_extension = audio_file_path.split('.')[-1].lower()
            
            # Map common extensions to formats
            format_mapping = {
                'flac': 'flac',
                'mp3': 'mp3',
                'm4a': 'm4a',
                'mpeg': 'mpeg',
                'mpga': 'mpga',
                'mp4': 'mp4',
                'ogg': 'ogg',
                'pcm': 'pcm',
                'wav': 'wav',
                'webm': 'webm'
            }
            
            if file_extension not in format_mapping:
                print(f"✗ Unsupported file format: {file_extension}")
                print(f"Supported formats: {', '.join(format_mapping.keys())}")
                return
            
            audio_format = format_mapping[file_extension]
            
            # Send audio format (only once for the entire session)
            print(f"Detected audio format: {audio_format}")
            await websocket.send(audio_format)
            
            # Step 3: Receive format confirmation
            format_response = await websocket.recv()
            print(f"✓ Format accepted: {format_response}\n")
            
            # Process files in a loop
            files_to_process = [audio_file_path]
            success_count = 0
            
            file_index = 0
            while file_index < len(files_to_process):
                file_path = files_to_process[file_index]
                print(f"\n[File {file_index + 1}]")
                
                if await send_file_for_analysis(websocket, file_path):
                    success_count += 1
                
                file_index += 1
                
                # Ask if user wants to process another file
                add_more = input("\nProcess another file? (y/n): ").strip().lower()
                if add_more == 'y':
                    next_file = input("Enter the path to the next audio file: ").strip()
                    if next_file and os.path.exists(next_file):
                        # Verify same format
                        next_extension = next_file.split('.')[-1].lower()
                        if next_extension == file_extension:
                            files_to_process.append(next_file)
                        else:
                            print(f"⚠ Warning: File format mismatch. Expected {file_extension}, got {next_extension}. Skipping.")
                    else:
                        print("⚠ File not found. Skipping.")
                else:
                    break
            
            print(f"\n{'='*60}")
            print(f"✓ Session complete: {success_count}/{len(files_to_process)} files analyzed successfully")
            print(f"{'='*60}")
            
            # Gracefully close connection
            print("\nClosing connection...")
            await websocket.send("CLOSE")
            close_msg = await websocket.recv()
            print(f"{close_msg}")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"✗ WebSocket error: {e}")
    except ConnectionRefusedError:
        print("✗ Connection refused. Make sure the server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket Audio Streaming Test - Instant Results")
    print("=" * 60)
    print("\nMake sure your FastAPI server is running first!")
    print("Run: python abc.py\n")
    print("How it works:")
    print("1. Connects to WebSocket (connection stays open)")
    print("2. Auto-detects audio format from first file")
    print("3. Sends entire file, then 'ANALYZE' command")
    print("4. Gets INSTANT analysis result")
    print("5. Can process more files without reconnecting")
    print("6. Gracefully closes when done\n")
    print("Supported formats: flac, mp3, m4a, mpeg, mpga, mp4, ogg, pcm, wav, webm\n")
    
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n\n✗ Test interrupted by user")
        sys.exit(0)
