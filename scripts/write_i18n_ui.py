"""Small UI strings outside the immutable page translation catalogue."""
from pathlib import Path
import json
ROWS = {
'fr': ['Langue','Mettre les aperçus en pause','Reprendre les aperçus',"Mettre l’aperçu en pause","Voir l’aperçu animé","Écrans de l’application rendus sur ordinateur, avec des données de démonstration. Les animations sont réalisées à partir de ces captures."],
'en': ['Language','Pause previews','Resume previews','Pause preview','View animated preview','App screens rendered on a computer with demonstration data. Animations are made from these screenshots.'],
'de': ['Sprache','Vorschauen anhalten','Vorschauen fortsetzen','Vorschau anhalten','Animierte Vorschau ansehen','Auf einem Computer gerenderte App-Bildschirme mit Beispieldaten. Die Animationen werden aus diesen Bildschirmaufnahmen erstellt.'],
'es': ['Idioma','Pausar las vistas previas','Reanudar las vistas previas','Pausar la vista previa','Ver la vista previa animada','Pantallas de la aplicación renderizadas en un ordenador con datos de demostración. Las animaciones se crean a partir de estas capturas.'],
'it': ['Lingua','Metti in pausa le anteprime','Riprendi le anteprime',"Metti in pausa l’anteprima",'Guarda l’anteprima animata','Schermate dell’app renderizzate su computer con dati dimostrativi. Le animazioni sono create a partire da queste schermate.'],
'nl': ['Taal','Voorbeelden pauzeren','Voorbeelden hervatten','Voorbeeld pauzeren','Geanimeerd voorbeeld bekijken','App-schermen op een computer weergegeven met demonstratiegegevens. De animaties zijn gemaakt op basis van deze schermafbeeldingen.'],
'pt': ['Idioma','Pausar pré-visualizações','Retomar pré-visualizações','Pausar pré-visualização','Ver pré-visualização animada','Ecrãs da aplicação renderizados num computador com dados de demonstração. As animações são criadas a partir destas capturas.'],
'pt-BR': ['Idioma','Pausar prévias','Retomar prévias','Pausar prévia','Ver prévia animada','Telas do aplicativo renderizadas em um computador com dados de demonstração. As animações são criadas a partir dessas capturas.'],
'pl': ['Język','Wstrzymaj podglądy','Wznów podglądy','Wstrzymaj podgląd','Zobacz animowany podgląd','Ekrany aplikacji wyrenderowane na komputerze z danymi demonstracyjnymi. Animacje powstały na podstawie tych zrzutów ekranu.'],
'ru': ['Язык','Приостановить просмотр','Возобновить просмотр','Приостановить анимацию','Посмотреть анимацию','Экраны приложения отрисованы на компьютере с демонстрационными данными. Анимации созданы на основе этих снимков экрана.'],
'uk': ['Мова','Призупинити перегляд','Відновити перегляд','Призупинити анімацію','Переглянути анімацію','Екрани застосунку відтворено на комп’ютері з демонстраційними даними. Анімації створено на основі цих знімків екрана.'],
'tr': ['Dil','Önizlemeleri duraklat','Önizlemeleri sürdür','Önizlemeyi duraklat','Animasyonlu önizlemeyi gör','Uygulama ekranları örnek verilerle bir bilgisayarda oluşturulmuştur. Animasyonlar bu ekran görüntülerinden hazırlanmıştır.'],
'ar': ['اللغة','إيقاف المعاينات مؤقتًا','استئناف المعاينات','إيقاف المعاينة مؤقتًا','عرض المعاينة المتحركة','شاشات التطبيق معروضة على الحاسوب باستخدام بيانات تجريبية. أُنشئت الرسوم المتحركة انطلاقًا من هذه اللقطات.'],
'hi': ['भाषा','पूर्वावलोकन रोकें','पूर्वावलोकन फिर शुरू करें','पूर्वावलोकन रोकें','एनिमेटेड पूर्वावलोकन देखें','ऐप की स्क्रीन कंप्यूटर पर उदाहरण डेटा के साथ रेंडर की गई हैं। एनिमेशन इन स्क्रीनशॉट से बनाए गए हैं।'],
'id': ['Bahasa','Jeda pratinjau','Lanjutkan pratinjau','Jeda pratinjau','Lihat pratinjau animasi','Layar aplikasi dirender di komputer dengan data demonstrasi. Animasi dibuat dari tangkapan layar ini.'],
'ja': ['言語','プレビューを一時停止','プレビューを再開','プレビューを一時停止','アニメーションを見る','デモデータを使用し、パソコン上で描画したアプリ画面です。アニメーションはこれらのスクリーンショットから作成しています。'],
'ko': ['언어','미리보기 일시정지','미리보기 재개','미리보기 일시정지','애니메이션 미리보기','데모 데이터를 사용해 컴퓨터에서 렌더링한 앱 화면입니다. 애니메이션은 이 스크린샷을 바탕으로 제작되었습니다.'],
'th': ['ภาษา','หยุดตัวอย่างชั่วคราว','เล่นตัวอย่างต่อ','หยุดตัวอย่างชั่วคราว','ดูตัวอย่างภาพเคลื่อนไหว','หน้าจอแอปแสดงผลบนคอมพิวเตอร์โดยใช้ข้อมูลสาธิต ภาพเคลื่อนไหวสร้างจากภาพหน้าจอเหล่านี้'],
'vi': ['Ngôn ngữ','Tạm dừng bản xem trước','Tiếp tục bản xem trước','Tạm dừng bản xem trước','Xem bản xem trước động','Màn hình ứng dụng được kết xuất trên máy tính với dữ liệu minh họa. Hoạt ảnh được tạo từ các ảnh chụp màn hình này.'],
'zh': ['语言','暂停预览','继续预览','暂停预览','观看动态预览','应用界面使用演示数据在电脑上渲染。动画由这些屏幕截图制作而成。'],
'zh-Hans': ['语言','暂停预览','继续预览','暂停预览','观看动态预览','应用界面使用演示数据在电脑上渲染。动画由这些屏幕截图制作而成。'],
'zh-Hant': ['語言','暫停預覽','繼續預覽','暫停預覽','觀看動態預覽','應用程式畫面使用示範資料在電腦上繪製。動畫由這些螢幕截圖製作而成。'],
}
KEYS=['language','pause_all','resume_all','pause_one','play_one','capture_note']
out={locale:dict(zip(KEYS,values,strict=True)) for locale,values in ROWS.items()}
(Path(__file__).resolve().parents[1]/'locales'/'ui.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
