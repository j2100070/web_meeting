// 共通のユーティリティ関数を定義
const CommonUtils = {
    // メールアドレスのバリデーション
    validateEmail: function(emailValue, participantList) {
        if (emailValue === "") {
            alert(`メールアドレスが空です: "${emailValue}"`);
            return false;
        }
        if (!emailValue.match(/^[a-zA-Z0-9!#$%&'*+\-/=?^_`{|}~.]+@[a-zA-Z0-9][a-zA-Z0-9-]*(\.[a-zA-Z0-9][a-zA-Z0-9-]*)*$/)) {
            alert(`メールアドレスの形式が正しくありません: "${emailValue}"`);
            return false;
        }
        if (
            participantList
                .find(".participant-mail")
                .filter(function () {
                    return $(this).attr("value") === emailValue;
                }).length > 0
        ) {
            alert(`メールアドレスは既に追加されています: "${emailValue}"`);
            return false;
        }
        return true;
    },

    // 参加者追加の共通処理
    addParticipant: function(participantList, emailInput) {
        var emailValue = emailInput.val().trim();

        // バリデーション関数を使用
        if (!this.validateEmail(emailValue, participantList)) {
            emailInput.focus();
            return;
        }

        // 参加者を追加
        emailValue.length = emailValue.length + 10;
        const newParticipant = $(`
            <div class="participant">
                <input type="email" name="participants[]" class="participant-mail" value="${emailValue}" size="${emailValue.length}" readonly>
                <img class="participant-delete" src="../static/img/72.png" alt="会議参加者を削除するクリックアイコンです。" >
            </div>
        `);

        // .participant-inputタグの直前に追加
        const participantInput = participantList.find('.participant-input').last();
        if (participantInput.length > 0) {
            newParticipant.insertBefore(participantInput);
        } else {
            participantList.append(newParticipant);
        }

        emailInput.val("");
    },

    // 日時フォーマット
    getFormattedDateTime: function(date) {
        let year = date.getFullYear();
        let month = ('0' + (date.getMonth() + 1)).slice(-2);
        let day = ('0' + date.getDate()).slice(-2);
        let hours = ('0' + date.getHours()).slice(-2);
        let minutes = ('0' + date.getMinutes()).slice(-2);
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    },

    // テキストエリアの高さ自動調整
    adjustTextareaHeight: function(textarea) {
        $(textarea).height('auto');
        $(textarea).height(textarea.scrollHeight);
    },

    // トグルチェックボックスのテキスト更新
    updateToggleText: function($checkbox) {
        const isChecked = $checkbox.prop("checked");
        const $toggleText = $checkbox.siblings(".toggle-text");

        let textOn = "ON";
        let textOff = "OFF";

        if ($checkbox.attr("name") === "is_guest_join") {
            textOn = "ゲスト参加OK";
            textOff = "ゲスト参加不可";
        } else if ($checkbox.attr("name") === "is_recurrence") {
            textOn = "繰り返す";
            textOff = "繰り返さない";
        } else if ($checkbox.attr("name") === "is_record") {
            textOn = "録画する";
            textOff = "録画しない";
        }

        $toggleText.text(isChecked ? textOn : textOff);
    }
};

// グローバルスコープに公開
window.CommonUtils = CommonUtils; 