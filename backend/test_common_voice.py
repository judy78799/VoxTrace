#!/usr/bin/env python3
"""
Common Voice 데이터셋 테스트 스크립트
Mozilla API를 통해 샘플을 다운로드하고 ASR 테스트
"""

import os
import sys
import json
import tarfile
import tempfile
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 설정
DATASET_ID = "cmu5rwtaf003dnq07e7n3q6tf"
API_URL = f"https://mozilladatacollective.com/api/datasets/{DATASET_ID}/download"

def download_dataset(api_key: str, output_dir: str):
    """API를 통해 데이터셋 다운로드"""
    print("🔄 Requesting download URL from Mozilla API...")

    # API 호출
    cmd = [
        'curl', '-X', 'POST', API_URL,
        '-H', f'Authorization: Bearer {api_key}',
        '-H', 'Content-Type: application/json',
        '-s'  # silent mode
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ API request failed: {result.stderr}")
        return None

    try:
        response = json.loads(result.stdout)
        download_url = response.get('downloadUrl')

        if not download_url:
            print(f"❌ No download URL in response: {result.stdout}")
            return None

        print(f"✅ Got download URL")

        # 다운로드
        tar_path = os.path.join(output_dir, "common-voice-korean.tar.gz")
        print(f"📥 Downloading dataset to {tar_path}...")
        print(f"   (This may take a while for large datasets)")

        download_cmd = ['curl', '-o', tar_path, download_url, '--progress-bar']
        subprocess.run(download_cmd, check=True)

        print(f"✅ Download complete")
        return tar_path

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse API response: {e}")
        print(f"   Response: {result.stdout}")
        return None
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None


def extract_samples(tar_path: str, output_dir: str, num_samples: int = 3):
    """압축 파일에서 샘플 MP3 파일 추출"""
    print(f"\n📦 Extracting {num_samples} sample files...")

    samples = []

    try:
        with tarfile.open(tar_path, 'r:gz') as tar:
            # 모든 멤버 리스트
            members = tar.getmembers()

            # clips/*.mp3 파일 찾기
            mp3_files = [m for m in members if m.name.endswith('.mp3') and 'clips/' in m.name]

            print(f"   Found {len(mp3_files)} MP3 files in archive")

            # 처음 N개만 추출
            for member in mp3_files[:num_samples]:
                print(f"   Extracting: {member.name}")
                tar.extract(member, output_dir)
                samples.append(os.path.join(output_dir, member.name))

        print(f"✅ Extracted {len(samples)} samples")
        return samples

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return []


def test_transcription(audio_file: str):
    """ASR 전사 테스트"""
    print(f"\n🎤 Testing transcription: {Path(audio_file).name}")

    # FastAPI 서버를 통해 테스트
    # 1. 파일 업로드
    upload_cmd = [
        'curl', '-X', 'POST',
        'http://127.0.0.1:8003/api/audio/upload',
        '-F', f'file=@{audio_file}',
        '-s'
    ]

    upload_result = subprocess.run(upload_cmd, capture_output=True, text=True)

    if upload_result.returncode != 0:
        print(f"❌ Upload failed: {upload_result.stderr}")
        return

    try:
        upload_response = json.loads(upload_result.stdout)
        file_id = upload_response.get('file_id')

        if not file_id:
            print(f"❌ No file_id in upload response")
            return

        print(f"✅ Uploaded (file_id: {file_id})")

        # 2. 전사 요청
        print(f"🔄 Transcribing...")

        transcribe_data = {
            'file_id': file_id,
            'language': 'ko',
            'enable_vad': True,
            'enable_diarization': False,
            'enable_enhancement': False
        }

        transcribe_cmd = [
            'curl', '-X', 'POST',
            'http://127.0.0.1:8003/api/audio/transcribe',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(transcribe_data),
            '-s'
        ]

        transcribe_result = subprocess.run(transcribe_cmd, capture_output=True, text=True)

        if transcribe_result.returncode != 0:
            print(f"❌ Transcription failed: {transcribe_result.stderr}")
            return

        transcribe_response = json.loads(transcribe_result.stdout)

        # 결과 출력
        print(f"\n{'='*60}")
        print(f"✅ Transcription Result")
        print(f"{'='*60}")
        print(f"Language: {transcribe_response.get('language')}")
        print(f"Processing Time: {transcribe_response.get('processing_time', 0):.2f}s")
        print(f"Segments: {len(transcribe_response.get('segments', []))}")

        if transcribe_response.get('rtf'):
            print(f"RTF: {transcribe_response['rtf']:.2f}x")

        # 첫 3개 세그먼트 출력
        segments = transcribe_response.get('segments', [])
        if segments:
            print(f"\n📝 Transcription Text (first 3 segments):")
            for i, seg in enumerate(segments[:3]):
                print(f"  [{i+1}] {seg['start']:.2f}s - {seg['end']:.2f}s")
                print(f"      {seg['text']}")
                if seg.get('confidence'):
                    print(f"      (confidence: {seg['confidence']*100:.1f}%)")

        print(f"{'='*60}\n")

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse response: {e}")
        print(f"   Response: {upload_result.stdout if 'upload' in str(e) else transcribe_result.stdout}")
    except Exception as e:
        print(f"❌ Test failed: {e}")


def main():
    """메인 함수"""
    print("🎤 VoxTrace - Common Voice Test Script")
    print("="*60)

    # API key 확인
    api_key = os.environ.get('MOZILLA_API_KEY')
    if not api_key:
        print("❌ MOZILLA_API_KEY not found in environment")
        print("   Please add it to backend/.env file:")
        print("   MOZILLA_API_KEY=your_api_key_here")
        sys.exit(1)

    print(f"✅ Using API key: {api_key[:8]}...")

    # 임시 디렉토리 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"📁 Working directory: {tmpdir}\n")

        # 1. 데이터셋 다운로드
        tar_path = download_dataset(api_key, tmpdir)

        if not tar_path:
            print("❌ Failed to download dataset")
            sys.exit(1)

        # 2. 샘플 추출
        samples = extract_samples(tar_path, tmpdir, num_samples=3)

        if not samples:
            print("❌ No samples extracted")
            sys.exit(1)

        # 3. 각 샘플 테스트
        for sample in samples:
            test_transcription(sample)

        print("\n✅ All tests completed!")


if __name__ == '__main__':
    main()
