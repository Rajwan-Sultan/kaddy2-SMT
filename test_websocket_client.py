import asyncio
import websockets
import json
import os

async def test_websocket():
    uri = "ws://localhost:8000/ws/analyze"
    
    async with websockets.connect(uri) as websocket:
        print("✓ Connected to WebSocket\n")
        
        segment_files = [
            # "segment_1.mp3",
            # "segment_2.mp3",
            # "segment_3.mp3",
            "scam.mp3",
            "scam2.mp3",
            "scam.mp3"
        ]
        
        for idx, segment_file in enumerate(segment_files):
            if not os.path.exists(segment_file):
                print(f"⚠ Warning: {segment_file} not found, skipping...")
                continue
            
            with open(segment_file, "rb") as f:
                audio_segment = f.read()
            
            print(f"\n→ Sending {segment_file} ({len(audio_segment)} bytes)")
            await websocket.send(audio_segment)
            
            # First file establishes connection
            if idx == 0:
                connected = await websocket.recv()
                connected_data = json.loads(connected)
                print(f"← {connected_data['message']}")
                print(f"   Timeout: {connected_data['config']['inactivity_timeout']}")
                print("="*70)
            
            ack = await websocket.recv()
            ack_data = json.loads(ack)
            print(f"← Segment #{ack_data['segment_number']} received")
            
            analyzing = await websocket.recv()
            analyzing_data = json.loads(analyzing)
            print(f"← {analyzing_data['message']}")
            
            result = await websocket.recv()
            result_data = json.loads(result)
            
            if result_data["type"] == "analysis":
                print("\n" + "="*70)
                print(f"SEGMENT #{result_data['segment_number']} ANALYSIS:")
                print("="*70)
                
                segment = result_data["segment_analysis"]
                print(f"Scam Detected: {segment['scam_detected']}")
                print(f"Confidence: {segment['confidence_score']}%")
                print(f"Explanation: {segment['explanation']}")
                
                if segment.get('scam_tags'):
                    tags = [tag['tag'] for tag in segment['scam_tags']]
                    print(f"Tags: {', '.join(tags)}")
                
                if segment.get('risk_factors'):
                    print(f"\nRisk Factors:")
                    for factor, score in segment['risk_factors'].items():
                        if score is not None and score > 0:
                            print(f"  - {factor.replace('_', ' ').title()}: {score}/10")
                
                print("\n" + "-"*70)
                print("CUMULATIVE ASSESSMENT:")
                print("-"*70)
                
                cumulative = result_data["cumulative_assessment"]
                print(f"Overall Verdict: {cumulative['overall_verdict'].upper()}")
                print(f"Segments Analyzed: {cumulative['segments_analyzed']}")
                print(f"Highest Confidence: {cumulative['highest_confidence']}%")
                print(f"  • Scam: {cumulative['scam_segments']}")
                print(f"  • Legitimate: {cumulative['legitimate_segments']}")
                print(f"  • Ambiguous: {cumulative['ambiguous_segments']}")
                
                if cumulative['all_detected_tags']:
                    print(f"\nAll Tags: {', '.join(cumulative['all_detected_tags'])}")
                
                print("="*70)
            
            await asyncio.sleep(0.5)
        
        # Test manual close (optional - uncomment to test)
        # print("\n→ Sending close command")
        # await websocket.send(json.dumps({"action": "close"}))
        # close_response = await websocket.recv()
        # print(f"← {json.loads(close_response)['message']}")
        
        # Test timeout (uncomment to test 30-second timeout)
        # print("\n⏱ Waiting for 30s timeout...")
        # timeout_response = await websocket.recv()
        # print(f"← {json.loads(timeout_response)['message']}")
        
        print("\n✓ Test completed\n")

if __name__ == "__main__":
    asyncio.run(test_websocket())