// ==UserScript==
// @name         전북교육연수원(jbstudy.kr) 자동 수강 매크로 v2.0
// @namespace    http://tampermonkey.net/
// @version      2.0
// @description  강의 도중 나타나는 확인 아이콘 자동 클릭, 이수율 90% 감지 후 다음 단계 자동 이동
// @author       AntiGravity
// @match        *://*.jbstudy.kr/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // ─────────────────────────────────────────────
    // ★ 설정값 (필요 시 수정)
    // ─────────────────────────────────────────────
    const CHECK_INTERVAL_MS = 2000;   // 감시 주기 (2초)
    const NEXT_DELAY_MS     = 3000;   // 90% 도달 후 다음으로 넘기기 전 대기 (3초)
    const COMPLETION_RATE   = 90;     // 이수 기준 진도율 (%)

    // ─────────────────────────────────────────────
    // 내부 상태
    // ─────────────────────────────────────────────
    let isMovingNext = false; // 다음 페이지 이동 중 중복 방지 플래그

    // ─────────────────────────────────────────────
    // 로그 유틸
    // ─────────────────────────────────────────────
    function log(msg) {
        console.log('[AntiGravity v2.0] ' + msg);
    }

    // ─────────────────────────────────────────────
    // 1. 현재 영상 진도율 계산 (Video.js 기준)
    // ─────────────────────────────────────────────
    function getVideoProgress() {
        try {
            // a) __evt__ 글로벌 플레이어 객체 시도
            if (typeof __evt__ !== 'undefined' && __evt__.player) {
                const duration = __evt__.player.duration ? __evt__.player.duration() : 0;
                const current  = __evt__.player.currentTime ? __evt__.player.currentTime() : 0;
                if (duration > 0) return (current / duration) * 100;
            }
            // b) videojs 글로벌 객체 폴백
            if (typeof videojs !== 'undefined') {
                const keys = Object.keys(videojs.players);
                if (keys.length > 0) {
                    const p = videojs.players[keys[0]];
                    if (p && p.duration() > 0) {
                        return (p.currentTime() / p.duration()) * 100;
                    }
                }
            }
        } catch (e) {}
        return -1; // 플레이어를 찾을 수 없음
    }

    // ─────────────────────────────────────────────
    // 2. 영상 재생 강제 시작 (일시정지 상태일 때)
    // ─────────────────────────────────────────────
    function ensurePlaying() {
        try {
            let player = null;
            if (typeof __evt__ !== 'undefined' && __evt__.player) {
                player = __evt__.player;
            } else if (typeof videojs !== 'undefined') {
                const keys = Object.keys(videojs.players);
                if (keys.length > 0) player = videojs.players[keys[0]];
            }
            if (player && player.paused && player.paused()) {
                log('▶ 영상이 일시정지 상태 → 강제 재생');
                player.play();
            }
        } catch (e) {}
    }

    // ─────────────────────────────────────────────
    // 3. 첫 번째 아이콘 처리
    //    강의 도중 나타나는 "재생 확인" / "퀴즈" / "attendance" 팝업 클릭
    // ─────────────────────────────────────────────
    function handleFirstIcon() {
        // ① 큰 재생 버튼 (vjs-big-play-button) - 영상이 멈추고 재생 버튼이 나타난 경우
        const bigPlayBtn = document.querySelector('button.vjs-big-play-button');
        if (bigPlayBtn && bigPlayBtn.offsetParent !== null) {
            log('🎯 첫 번째 아이콘(빅 재생 버튼) 감지 → 클릭');
            bigPlayBtn.click();
            return true;
        }

        // ② 퀴즈 팝업이 열려있으면 닫기 (quizPage / quizShowBtn)
        const quizPage = document.querySelector('.quizPage');
        if (quizPage && getComputedStyle(quizPage).display !== 'none') {
            log('🎯 퀴즈 팝업 감지 → 숨기고 재생 재개');
            const quizBtn = document.querySelector('.quizShowBtn');
            if (quizBtn) quizBtn.style.display = 'none';
            quizPage.style.display = 'none';
            const playerBox = document.querySelector('.player_box');
            if (playerBox) playerBox.style.display = '';
            ensurePlaying();
            return true;
        }

        // ③ 일반 팝업/모달 오버레이 - "확인" 버튼 자동 클릭
        //    (수강 중 무작위로 뜨는 "학습 중입니까?" 류 팝업)
        const popupSelectors = [
            '.pop_attend .btn_attend',      // 출석 확인 버튼
            '.attend_check_btn',
            '.popupAttend button',
            '[class*="attend"] button',
            '[id*="attend"] button',
            '.popup_wrap .btn_confirm',
            '.layer_popup .btn_ok',
            '.btn_popup_confirm',
        ];
        for (const sel of popupSelectors) {
            const el = document.querySelector(sel);
            if (el && el.offsetParent !== null) {
                log('🎯 팝업 확인 버튼 감지 (' + sel + ') → 클릭');
                el.click();
                ensurePlaying();
                return true;
            }
        }

        return false;
    }

    // ─────────────────────────────────────────────
    // 4. 이수율 팝업에서 퍼센트 읽기
    //    화면에 이수율 창이 떠 있을 때 숫자를 파싱
    // ─────────────────────────────────────────────
    function readCompletionPopup() {
        // 이수율을 표시하는 팝업/레이어를 찾아 숫자 추출
        const candidates = document.querySelectorAll(
            '[class*="rate"], [class*="Rate"], [class*="progress"], [class*="isu"], [id*="rate"], [id*="isu"]'
        );
        for (const el of candidates) {
            const text = el.innerText || '';
            const match = text.match(/(\d+(\.\d+)?)\s*%/);
            if (match) {
                const pct = parseFloat(match[1]);
                if (pct > 0 && pct <= 100) {
                    log('📊 이수율 팝업에서 진도율 감지: ' + pct + '%');
                    return pct;
                }
            }
        }
        return -1;
    }

    // ─────────────────────────────────────────────
    // 5. 두 번째 아이콘 처리 (90% 도달 후)
    //    강의 화면을 먼저 클릭 → playerBtnafter 아이콘 클릭
    // ─────────────────────────────────────────────
    function handleSecondIcon() {
        // 강의 화면(영상 영역) 클릭
        const videoEl = document.querySelector('.vjs-tech, video');
        if (videoEl) {
            log('🖱️ 강의 화면 클릭');
            videoEl.click();
        }

        // playerBtnafter 아이콘 (two-icon / next-action icon)
        const btnAfter = document.querySelector('.playerBtnafter, .playerBtnafter.on, [class*="playerBtn"]');
        if (btnAfter && btnAfter.offsetParent !== null) {
            log('🎯 두 번째 아이콘(playerBtnafter) 감지 → 클릭');
            btnAfter.click();
            return true;
        }

        // 폴백: 다음 차시 버튼 직접 클릭
        const nextBtn = document.querySelector('a.btn_cousre.next, .btn_next_cls, .btnNextStep');
        if (nextBtn && nextBtn.offsetParent !== null && !nextBtn.classList.contains('disabled')) {
            log('🎯 다음 차시 버튼 감지 → 클릭');
            nextBtn.click();
            return true;
        }

        // 폴백2: evt.js nextPage() 함수 호출
        try {
            if (typeof __evt__ !== 'undefined' && typeof __evt__.fn === 'function' && typeof __evt__.fn().nextPage === 'function') {
                log('🎯 __evt__.fn().nextPage() 강제 호출');
                __evt__.fn().nextPage();
                return true;
            }
        } catch (e) {}

        // 폴백3: cmplPageCnt 강제 이수 처리
        try {
            if (typeof cmplPageCnt !== 'undefined' && typeof pageIndex !== 'undefined') {
                cmplPageCnt[(pageIndex - 1)] = 'Y';
                log('✅ cmplPageCnt 강제 이수 처리 완료');
            }
            if (typeof updateTime === 'function') {
                updateTime('video_Cmpl');
                updateTime('html_Cmpl');
                log('✅ updateTime() 강제 호출 완료');
            }
        } catch (e) {}

        return false;
    }

    // ─────────────────────────────────────────────
    // 6. 메인 감시 루프
    // ─────────────────────────────────────────────
    function mainLoop() {
        // A. 첫 번째 아이콘 처리 (항상 우선)
        handleFirstIcon();

        // B. 진도율 측정 (영상 기준 또는 이수율 팝업 기준)
        let progress = getVideoProgress();

        // 이수율 팝업이 떠 있다면 거기서 읽기
        const popupProgress = readCompletionPopup();
        if (popupProgress > 0) progress = popupProgress;

        if (progress < 0) return; // 플레이어 미감지

        log('📈 현재 진도율: ' + progress.toFixed(1) + '%');

        // C. 90% 도달 시 두 번째 아이콘 처리
        if (progress >= COMPLETION_RATE && !isMovingNext) {
            isMovingNext = true;
            log('🏆 이수율 ' + COMPLETION_RATE + '% 달성! ' + NEXT_DELAY_MS / 1000 + '초 후 다음 단계로 이동합니다...');

            setTimeout(function() {
                handleSecondIcon();
                // 다음 영상을 위해 플래그 초기화 (5초 후)
                setTimeout(function() {
                    isMovingNext = false;
                    log('🔄 다음 영상을 위해 플래그 초기화 완료');
                }, 5000);
            }, NEXT_DELAY_MS);
        }
    }

    // ─────────────────────────────────────────────
    // 시작
    // ─────────────────────────────────────────────
    log('🤖 AntiGravity 자동 수강 매크로 v2.0 시작됨! (전북교육연수원 전용)');
    log('⏱️ 감시 주기: ' + CHECK_INTERVAL_MS + 'ms | 이수 기준: ' + COMPLETION_RATE + '%');
    setInterval(mainLoop, CHECK_INTERVAL_MS);

})();
