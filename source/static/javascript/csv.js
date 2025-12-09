$(function(){
    function setupCSVEmailUploader(uploadButtonId, fileInputId, containerId) {
      $(uploadButtonId).on('click', function(event) {
        event.preventDefault();
        $(fileInputId).click();
      });
      
      $(fileInputId).on('change', function(event) {
        var file = event.target.files[0];
        if (file) {
          var fileExtension = file.name.split('.').pop().toLowerCase();
          if (fileExtension !== 'csv') {
            alert('CSVファイルを選択してください。');
            return;
          }
          Papa.parse(file, {
            complete: function(results) {
              // 既存の参加者リストはクリアせず、新しい参加者を追加する
              var emailString = results.data.join(',');
              var emailList = emailString.split(',');
              var participantList = $(containerId);
              var emailInput = $('input[name="participant-email"]');
              
              // 各メールアドレスを追加
              emailList.forEach(function(email) {
                if (email && email.trim() !== '') {
                  // 一時的にemailInputの値を設定
                  emailInput.val(email.trim());
                  // CommonUtils.addParticipantを使用して参加者を追加
                  CommonUtils.addParticipant(participantList, emailInput);
                  emailInput.val('');
                }
              });
              
              // ファイル入力をクリア
              $(fileInputId).val('');
            },
            error: function(err) {
              console.error('CSVファイルの読み込みエラー:', err);
            }
          });
        }
      });
    }
    
    // ゲストアイコンへのメールアドレス一括追加機能の設定
    setupCSVEmailUploader(
      '#uploadCSVButton',
      '#emailCSV_input',
      '.participant-list'
    );
    
    // 必要に応じて他の場所でも同じ機能を使用できる
    // 例: setupCSVEmailUploader('#otherUploadButton', '#otherFileInput', '#otherContainer');
  });