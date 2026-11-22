export const languages = { en: 'English', te: 'తెలుగు', hi: 'हिन्दी' }
export type Language = keyof typeof languages

interface Copy {
  skip: string
  menu: string
  language: string
  nav: [string, string, string, string]
  hero: [string, string, string]
  intro: string
  philosophy: string
  belief: string
  product: string
  serviceTitle: string
  services: [string, string][]
  processTitle: string
  steps: string[]
  languageTitle: string
  languageBody: string
  demoTitle: string
  demoNote: string
  exchanges: [string, string][]
  you: string
  close: string
  cta: string
  call: string
  top: string
}
export const copy: Record<Language, Copy> = {
  en: {
    skip: 'Skip to content', menu: 'Menu', language: 'Page language',
    nav: ['The idea', 'Services', 'How it works', 'Try a demo'],
    hero: ['One number.', 'Any service.', 'Your language.'],
    intro: 'An AI voice receptionist for restaurant tables and doctor appointments.',
    philosophy: 'Voice is the most natural interface.',
    belief: 'Language should never stand between people and everyday services.',
    product: 'Vaani answers the phone, listens to what you need, and helps you make a booking. Use the phone you already have. There’s no app to install.',
    serviceTitle: 'Two ways to book by voice.',
    services: [['Restaurant reservations', 'Ask for a table, share your party size and preferred time, and confirm an available slot.'], ['Hospital appointments', 'Ask for a doctor’s appointment and choose a time that works for you.']],
    processTitle: 'From hello to booking.',
    steps: ['Call Vaani.', 'Say what you need in your language.', 'Hear the available options.', 'Confirm your choice.', 'Hear the booking outcome.'],
    languageTitle: 'Speak the way you speak.',
    languageBody: 'Vaani is designed for Telugu, Hindi and Indian English, including the way people switch between languages in one conversation.',
    demoTitle: 'A conversation is all it takes.',
    demoNote: 'This is a sample transcript. No call is placed and no booking is made.',
    exchanges: [['Can I get a table for four tomorrow evening?', 'There’s a table at 7:30 pm. Would you like that?'], ['I’d like an appointment with a general physician.', 'There’s a slot tomorrow at 10 am. Does that work?']],
    you: 'Caller', close: 'Close demo', cta: 'Read a sample call', call: 'Call Vaani', top: 'Back to top',
  },
  te: {
    skip: 'విషయానికి వెళ్లండి', menu: 'మెనూ', language: 'పేజీ భాష',
    nav: ['ఆలోచన', 'సేవలు', 'ఎలా పనిచేస్తుంది', 'డెమో'],
    hero: ['ఒకే నంబర్.', 'ఏ సేవైనా.', 'మీ భాషలో.'],
    intro: 'రెస్టారెంట్ టేబుల్‌లు, డాక్టర్ అపాయింట్‌మెంట్‌ల కోసం ఏఐ వాయిస్ రిసెప్షనిస్ట్.',
    philosophy: 'మాట్లాడటం మనకు సహజం.',
    belief: 'రోజువారీ సేవలు పొందడానికి భాష అడ్డంకి కాకూడదు.',
    product: 'వాణి మీ కాల్‌కి సమాధానం ఇచ్చి, మీ అవసరాన్ని విని బుకింగ్‌లో సహాయపడుతుంది. మీ ఫోన్ చాలు. యాప్ అవసరం లేదు.',
    serviceTitle: 'మాట్లాడి బుక్ చేసుకునే రెండు సేవలు.',
    services: [['రెస్టారెంట్ టేబుల్', 'ఎంతమందికి, ఏ సమయానికి టేబుల్ కావాలో చెప్పండి. అందుబాటులో ఉన్న సమయాన్ని ఎంచుకోండి.'], ['డాక్టర్ అపాయింట్‌మెంట్', 'డాక్టర్ అపాయింట్‌మెంట్ అడిగి, మీకు సరిపోయే సమయాన్ని ఎంచుకోండి.']],
    processTitle: 'హలో నుంచి బుకింగ్ వరకు.',
    steps: ['వాణికి కాల్ చేయండి.', 'మీ అవసరాన్ని మీ భాషలో చెప్పండి.', 'అందుబాటులో ఉన్న ఎంపికలు వినండి.', 'మీ ఎంపికను నిర్ధారించండి.', 'బుకింగ్ ఫలితం వినండి.'],
    languageTitle: 'మీకు సహజంగా అనిపించేలా మాట్లాడండి.',
    languageBody: 'వాణి తెలుగు, హిందీ, భారతీయ ఇంగ్లీష్ కోసం రూపొందింది. ఒకే సంభాషణలో భాషలు కలిపి మాట్లాడవచ్చు.',
    demoTitle: 'ఒక చిన్న సంభాషణ చాలు.',
    demoNote: 'ఇది నమూనా సంభాషణ. కాల్ చేయబడదు, బుకింగ్ జరగదు.',
    exchanges: [['రేపు సాయంత్రం నలుగురికి టేబుల్ దొరుకుతుందా?', 'సాయంత్రం 7:30కి టేబుల్ ఉంది. ఆ సమయం సరిపోతుందా?'], ['జనరల్ ఫిజీషియన్ అపాయింట్‌మెంట్ కావాలి.', 'రేపు ఉదయం 10 గంటలకు సమయం ఉంది. మీకు సరిపోతుందా?']],
    you: 'కాలర్', close: 'డెమో మూసివేయండి', cta: 'నమూనా కాల్ చదవండి', call: 'వాణికి కాల్ చేయండి', top: 'పైకి వెళ్లండి',
  },
  hi: {
    skip: 'मुख्य सामग्री पर जाएँ', menu: 'मेनू', language: 'पेज की भाषा',
    nav: ['विचार', 'सेवाएँ', 'कैसे काम करता है', 'डेमो देखें'],
    hero: ['एक नंबर।', 'कोई भी सेवा।', 'आपकी भाषा।'],
    intro: 'रेस्तराँ में टेबल और डॉक्टर की अपॉइंटमेंट के लिए एआई वॉइस रिसेप्शनिस्ट।',
    philosophy: 'बात करना सबसे सहज है।',
    belief: 'रोज़मर्रा की सेवाएँ पाने में भाषा बाधा नहीं बननी चाहिए।',
    product: 'वाणी फ़ोन उठाती है, आपकी ज़रूरत सुनती है और बुकिंग में मदद करती है। अपना फ़ोन इस्तेमाल करें। किसी ऐप की ज़रूरत नहीं है।',
    serviceTitle: 'बात करके बुक करने के दो तरीके।',
    services: [['रेस्तराँ में टेबल', 'बताएँ कितने लोग हैं और किस समय आना है। फिर उपलब्ध समय पक्का करें।'], ['डॉक्टर की अपॉइंटमेंट', 'डॉक्टर की अपॉइंटमेंट माँगें और अपने लिए सुविधाजनक समय चुनें।']],
    processTitle: 'हैलो से बुकिंग तक।',
    steps: ['वाणी को कॉल करें।', 'अपनी ज़रूरत अपनी भाषा में बताएँ।', 'उपलब्ध विकल्प सुनें।', 'अपनी पसंद पक्की करें।', 'बुकिंग का नतीजा सुनें।'],
    languageTitle: 'जैसे बोलते हैं, वैसे ही बोलें।',
    languageBody: 'वाणी को तेलुगु, हिंदी और भारतीय अंग्रेज़ी के लिए बनाया गया है। आप एक ही बातचीत में भाषाएँ मिला सकते हैं।',
    demoTitle: 'बस एक बातचीत की ज़रूरत है।',
    demoNote: 'यह नमूना बातचीत है। इससे कॉल या बुकिंग नहीं होती।',
    exchanges: [['कल शाम चार लोगों के लिए टेबल मिलेगी?', 'शाम 7:30 बजे एक टेबल उपलब्ध है। क्या वह समय ठीक है?'], ['मुझे जनरल फ़िज़िशियन की अपॉइंटमेंट चाहिए।', 'कल सुबह 10 बजे का समय उपलब्ध है। क्या वह ठीक है?']],
    you: 'कॉलर', close: 'डेमो बंद करें', cta: 'नमूना कॉल पढ़ें', call: 'वाणी को कॉल करें', top: 'ऊपर जाएँ',
  },
}
