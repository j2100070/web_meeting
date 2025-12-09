$(function(){
    var emailInput = $('input[name="participant-email"]');
    
    // 参加者追加ボタンのクリックイベント
    $("#add-participant").click(function() {
        CommonUtils.addParticipant($('.participant-list'), emailInput);
    });

    // IMEの変換状態を追跡する変数
    let isComposing = false;

    // IMEの変換開始時
    emailInput.on('compositionstart', function() {
        isComposing = true;
    });

    // IMEの変換終了時
    emailInput.on('compositionend', function() {
        isComposing = false;
    });

    // Enterキーが押された時の処理
    emailInput.on('keydown', function(e) {
        if (e.key === 'Enter' && !isComposing) {
            e.preventDefault();
            CommonUtils.addParticipant($('.participant-list'), emailInput);
        }
    });

    // 参加者削除ボタンのクリックイベント
    $(document).on("click", ".participant-delete", function () {
        var participant = $(this).parent();
        participant.remove();
    });

    // スクロール制御
    let timeout;
    $(".v-hide-scroll").on("mouseenter", function () {
        $(this).removeClass("v-hide-scroll");
        $(this).addClass("v-can-scroll");
        clearTimeout(timeout);
    }).on("mouseleave", function () {
        timeout = setTimeout(function () {
            $(this).removeClass("v-can-scroll");
            $(this).addClass("v-hide-scroll");
        }.bind(this), 100);
    });

    let timeout2;
    $(".h-hide-scroll").on("mouseenter", function () {
        $(this).removeClass("h-hide-scroll");
        $(this).addClass("h-can-scroll");
        clearTimeout(timeout2);
    }).on("mouseleave", function () {
        timeout2 = setTimeout(function () {
            $(this).removeClass("h-can-scroll");
            $(this).addClass("h-hide-scroll");
        }.bind(this), 5);
    });

    // 日時設定
    const defaultValue = $('#datetime').val();
    if (defaultValue) {
        return;
    }
    
    function setDateTime() {
        let now = new Date();
        now.setHours(now.getHours(), now.getMinutes(), 0, 0);
    
        let nextMonth = new Date();
        nextMonth.setMonth(nextMonth.getMonth() + 1);
        nextMonth.setHours(nextMonth.getHours(), nextMonth.getMinutes(), 0, 0);
    
        $("#datetime").val(CommonUtils.getFormattedDateTime(now));
        $("#datetime").attr("min", CommonUtils.getFormattedDateTime(now));
        $("#datetime").attr("max", CommonUtils.getFormattedDateTime(nextMonth));
    }
    
    setDateTime();
    $("#datetime").on("input", function() {
        let selectedDate = new Date($(this).val());
        let now = new Date();
        let nextMonth = new Date();
        nextMonth.setMonth(nextMonth.getMonth() + 1);

        if (selectedDate < now) {
            alert("過去の日程は選択できません。");
            setDateTime();
        } else if (selectedDate > nextMonth) {
            alert("1か月以上先の日程は選択できません。");
            setDateTime();
        }
    });

    // トグルチェックボックスの処理
    const $checkbox = $(".toggle-checkbox");
    $checkbox.each(function() {
        CommonUtils.updateToggleText($(this));
    });
    $checkbox.on("change", function() {
        CommonUtils.updateToggleText($(this));
    });

    // フォーム送信時の処理
    $("form").on("submit", function(e) {
        const $submitButton = $(this).find('button[type="submit"]');
        $submitButton.prop("disabled", true);
        $submitButton.text("送信中...");
        return true;
    });

    // メール本文の自動リサイズ機能
    const mailTextarea = $('textarea[name="mail_text"]');
    if (mailTextarea.length > 0) {
        mailTextarea.on('input', function() {
            CommonUtils.adjustTextareaHeight(this);
        });
        CommonUtils.adjustTextareaHeight(mailTextarea[0]);
    }
});

// 繰り返し設定の処理
$(document).on('change', '.is-recurrence', function(){
    const recurrenceDaysInput = $('#recurrence-days');
    if ($(this).is(':checked')) {
        recurrenceDaysInput.prop('disabled', false);
    } else {
        recurrenceDaysInput.prop('disabled', true);
        recurrenceDaysInput.val("");
    }
});