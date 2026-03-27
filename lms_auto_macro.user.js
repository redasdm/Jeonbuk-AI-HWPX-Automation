// ==UserScript==
// @name         중앙교육연수원(배움누리터) 자동 수강 매크로
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  비디오 시청 완료(90% 이상) 시 알아서 다음 페이지로 넘어가며, 돌발 팝업을 스킵합니다.
// @match        *://*.jbstudy.kr/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    let isCompleted = false;

    function autoNextMacro() {
        // 1. 플레이어 상태 확인
        if (typeof __evt__ !== "undefined" && __evt__.player && __evt__.player.duration && __evt__.player.duration() > 0) {
            
            let currentTime = __evt__.player.currentTime();
            let duration = __evt__.player.duration();
            let percentage = (currentTime / duration) * 100;

            // (선택 사항) 영상 배속을 높이려면 아래 주석(//)을 해제하세요. 
            // 단, 서버에서 비정상적인 체류시간(어뷰징)을 검사할 수 있으므로 주의해서 사용해야 합니다.
            // if (__evt__.player.playbackRate() < 2.0) {
            //     __evt__.player.playbackRate(2.0); 
            // }

            // 2. 진행률이 90% 이상이고, 아직 다음 넘기기 처리를 안 했다면 진입
            if (percentage >= 90 && !isCompleted) {
                isCompleted = true; // 중복 실행 잠금
                console.log("[AntiGravity 매크로] 🎯 영상 90% 도달! 다음 페이지로 이동을 준비합니다.");

                // 3. 확실한 처리를 위한 강제 이수 함수 호출
                try {
                    if(typeof cmplPageCnt !== "undefined" && typeof pageIndex !== "undefined") { 
                        cmplPageCnt[(pageIndex-1)] = "Y"; 
                    }
                    if(typeof updateTime === "function") { 
                        updateTime("video_Cmpl"); 
                        updateTime("html_Cmpl"); 
                    }
                } catch (e) {
                    console.log("[AntiGravity 매크로] 강제 이수 처리 중 오류 (무시됨):", e);
                }

                // 4. 진도율이 서버로 전송될 시간을 충분히 주기 위해 4초 대기 후 넥스트 액션 실행!
                setTimeout(function() {
                    console.log("[AntiGravity 매크로] 🚀 다음 차시/페이지 버튼 자동 클릭!");
                    
                    try {
                        // a) HTML 구조 상의 "다음 차시" 버튼이 활성화되어 있다면 클릭
                        if (typeof $ !== "undefined" && $('.btn_cousre.next').length > 0 && $('.btn_cousre.next').is(':visible') && !$('.btn_cousre.next').hasClass('disabled')) {
                            $('.btn_cousre.next')[0].click(); 
                        } 
                        // b) 차시 내부의 세부 단계(페이지)가 남아있다면 evt.js 내장함수 강제 호출
                        else if (typeof __evt__.fn === "function" && typeof __evt__.fn().nextPage === "function") {
                            __evt__.fn().nextPage(); 
                        } else {
                            console.log("[AntiGravity 매크로] 다음 버튼을 찾을 수 없거나 이미 마지막 페이지입니다.");
                        }
                    } catch (e) {
                         console.log("[AntiGravity 매크로] 다음 페이지 이동 중 오류:", e);
                    }

                    // 5. 페이지 이동 후 다음 영성을 위해 5초 뒤 플래그 초기화
                    setTimeout(() => { isCompleted = false; }, 5000);

                }, 4000); // 4초 대기 (안정성 확보)
            }
        }
        
        // --- 퀴즈 창이나 돌발 팝업이 뜨면 알아서 숨기고 재생 이어나가기 ---
        try {
            if (typeof $ !== "undefined" && $('.quizPage').is(':visible')) {
                console.log("[AntiGravity 매크로] 방해되는 퀴즈 팝업 창을 숨깁니다.");
                $('.quizShowBtn').hide();
                $('.quizPage').css('display','none');
                $(".player_box").show();
                
                // 퀴즈를 스킵하더라도 비디오가 일시 정지되어 있다면 다시 강제 재생
                if (__evt__ && __evt__.player && __evt__.player.paused()) {
                    __evt__.player.play();
                }
            }
        } catch (e) {}
    }

    // 매 2초(2000ms)마다 백그라운드에서 감시자 함수를 무한 반복 실행
    console.log("🤖 [AntiGravity 매크로 시작됨] 자동 수강 넘기기 감시 시스템 정상 작동 완료!");
    setInterval(autoNextMacro, 2000);

})();
