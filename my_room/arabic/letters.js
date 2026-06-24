// shared letter data for the arabic studio (explore + practice)
// [char, name, translit, sound, example_ar, example_translit, example_en]
window.LETTERS = [
  ["ا","alif","ʾalif","long \"aa\" — also the seat for vowels","أسد","asad","lion"],
  ["ب","bāʾ","b","\"b\" as in book","باب","bāb","door"],
  ["ت","tāʾ","t","\"t\" as in top","تفاح","tuffāḥ","apple"],
  ["ث","thāʾ","th","\"th\" as in think","ثعلب","thaʿlab","fox"],
  ["ج","jīm","j / g","Egyptian \"g\" as in go (\"j\" elsewhere)","جمل","gamal","camel"],
  ["ح","ḥāʾ","ḥ","breathy \"h\" from the throat","حصان","ḥiṣān","horse"],
  ["خ","khāʾ","kh","\"kh\" — like clearing your throat","خبز","khubz","bread"],
  ["د","dāl","d","\"d\" as in dog","دب","dubb","bear"],
  ["ذ","dhāl","dh","\"th\" as in this","ذهب","dhahab","gold"],
  ["ر","rāʾ","r","rolled \"r\"","رمان","rummān","pomegranate"],
  ["ز","zāy","z","\"z\" as in zoo","زهرة","zahra","flower"],
  ["س","sīn","s","\"s\" as in sun","سمك","samak","fish"],
  ["ش","shīn","sh","\"sh\" as in shoe","شمس","shams","sun"],
  ["ص","ṣād","ṣ","heavy / emphatic \"s\"","صقر","ṣaqr","falcon"],
  ["ض","ḍād","ḍ","heavy \"d\" — arabic is called \"the language of ḍād\"","ضفدع","ḍifdaʿ","frog"],
  ["ط","ṭāʾ","ṭ","heavy \"t\"","طائر","ṭāʾir","bird"],
  ["ظ","ẓāʾ","ẓ","heavy \"th/z\"","ظرف","ẓarf","envelope"],
  ["ع","ʿayn","ʿ","deep throat sound — no english equivalent","عين","ʿayn","eye"],
  ["غ","ghayn","gh","like a french \"r\" / soft gargle","غزال","ghazāl","gazelle"],
  ["ف","fāʾ","f","\"f\" as in fish","فيل","fīl","elephant 🐘"],
  ["ق","qāf","q","deep \"k\" from the back (Egyptian: a glottal stop)","قمر","qamar","moon"],
  ["ك","kāf","k","\"k\" as in kite","كلب","kalb","dog"],
  ["ل","lām","l","\"l\" as in love","ليمون","laymūn","lemon"],
  ["م","mīm","m","\"m\" as in moon","ماء","māʾ","water"],
  ["ن","nūn","n","\"n\" as in nose","نجمة","nagma","star"],
  ["ه","hāʾ","h","soft \"h\" as in hello","هلال","hilāl","crescent"],
  ["و","wāw","w / ū","\"w\" — or a long \"oo\"","وردة","warda","rose"],
  ["ي","yāʾ","y / ī","\"y\" — or a long \"ee\"","يد","yad","hand"]
];
// zero-width joiner — lets the browser shape positional forms live
window.ZWJ = "‍";
// letters that never connect to the letter AFTER them
window.NONCONNECT = "ادذرزو".split("");
