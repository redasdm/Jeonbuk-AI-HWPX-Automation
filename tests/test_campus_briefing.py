# tests/test_campus_briefing.py
import os
from pathlib import Path
import subprocess

def test_campus_briefing_generation():
    output_dir = Path("C:/Users/redas/OneDrive/Desktop/업무/보고자료")
    output_file = output_dir / "미래교육캠퍼스_연계_맞춤형_진로_성장_체계_구축_방안_보고요지.hwpx"
    
    # 이전 파일이 존재한다면 삭제
    if output_file.exists():
        output_file.unlink()
        
    print("기존 보고요지 파일 삭제 완료 (존재 시).")
    
    # 생성 스크립트 실행
    print("create_campus_briefing_plan.py 실행 시도...")
    result = subprocess.run(
        ["python", "create_campus_briefing_plan.py"],
        capture_output=True,
        text=True,
        check=True
    )
    print("스크립트 실행 완료.")
    
    # HWPX 파일 생성 여부 검증
    assert output_file.exists(), "HWPX 파일이 정상적으로 생성되지 않았습니다."
    assert output_file.stat().st_size > 10000, f"HWPX 파일 용량이 비정상적입니다: {output_file.stat().st_size} bytes"
    print(f"테스트 통과: HWPX 파일이 성공적으로 생성되었습니다 (크기: {output_file.stat().st_size} bytes)")

if __name__ == "__main__":
    test_campus_briefing_generation()
