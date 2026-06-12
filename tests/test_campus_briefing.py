# tests/test_campus_briefing.py
import os
from pathlib import Path
import subprocess

def test_campus_briefing_generation():
    output_dir = Path("C:/Users/redas/OneDrive/Desktop/업무/보고자료")
    output_file = output_dir / "미래교육캠퍼스_연계_맞춤형_진로_성장_체계_구축_방안_보고요지.hwpx"
    
    # 이전 파일이 존재한다면 삭제 시도
    if output_file.exists():
        try:
            output_file.unlink()
            print("기존 보고요지 파일 삭제 완료.")
        except PermissionError:
            print("\n[경고] 생성할 한글 파일이 한컴오피스 등에서 열려 있습니다.")
            print("파일을 닫고 다시 실행하시거나, 아래 생성된 새 파일을 확인하세요.\n")
            # 겹치지 않게 다른 파일 이름으로 저장하게끔 조치하지는 않으나 테스트 진행을 위해 표시
        
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
    if output_file.exists():
        assert output_file.stat().st_size > 1000, f"HWPX 파일 용량이 비정상적입니다: {output_file.stat().st_size} bytes"
        print(f"테스트 통과: HWPX 파일이 성공적으로 갱신되었습니다 (크기: {output_file.stat().st_size} bytes)")
    else:
        # PermissionError 등으로 파일 갱신이 막혔을 경우
        print("테스트 실패: 파일이 잠겨 있어 새 파일로 덮어쓸 수 없습니다.")
        raise PermissionError("출력 한글 파일이 열려 있어 갱신 불가 상태입니다.")

if __name__ == "__main__":
    test_campus_briefing_generation()
