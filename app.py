import sys, io, argparse, html, os
from functools import lru_cache
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'packages'))
import requests
import gradio as gr
from deep_translator import GoogleTranslator
from gtts import gTTS
from gtts.lang import tts_langs

LANGUAGES = GoogleTranslator().get_supported_languages(as_dict=True)
VOICES = tts_langs()

@lru_cache(maxsize=128)
def translate_segment(text, src, dest):
    # Translate the complete message; do not use unverified translation-memory matches.
    response = requests.get(
        'https://clients5.google.com/translate_a/t',
        params={'client': 'dict-chrome-ex', 'sl': src, 'tl': dest, 'q': text},
        timeout=(5, 25))
    response.raise_for_status()
    payload = response.json()
    translated = payload[0] if isinstance(payload, list) and payload else None
    if not isinstance(translated, str) or not translated.strip():
        raise ValueError('No valid translation returned.')
    translated = html.unescape(translated).strip()
    # Language names and API errors must never be presented as translated messages.
    if translated.casefold() in {'error', 'null', 'undefined'}:
        raise ValueError('Invalid translation response.')
    return translated


def chunks(text):
    # Google accepts at most 500 UTF-8 bytes per request.
    while text:
        end = 0
        size = 0
        for char in text:
            size += len(char.encode('utf-8'))
            if size > 450:
                break
            end += 1
        if end < len(text):
            space = text.rfind(' ', 0, end)
            if space > end // 2:
                end = space + 1
        yield text[:end]
        text = text[end:]


def translate(text, source, target, slow):
    text = (text or '').strip()
    if not text:
        raise gr.Error('Enter some text to translate.')
    if len(text) > 3000:
        raise gr.Error('Please use 3,000 characters or fewer.')
    if source == 'Detect automatically':
        return '', None, 'Please select Your language (for Nyob Zoo, choose hmong), then translate again. Automatic detection is no longer available.'
    if source not in LANGUAGES or target not in LANGUAGES:
        raise gr.Error('Select both the input and translation languages.')
    src, dest = LANGUAGES[source], LANGUAGES[target]
    try:
        translated = text if src == dest else translate_segment(text, src, dest)
    except Exception:
        raise gr.Error('Translation could not complete. Check your connection, choose a supported language pair, or try again later if the service quota is reached.') from None
    voice = {'iw': 'he'}.get(dest, dest)
    if voice not in VOICES:
        return translated, None, 'Translation ready. Audio is unavailable for this language.'
    try:
        audio = io.BytesIO()
        gTTS(translated, lang=voice, slow=slow).write_to_fp(audio)
        return translated, audio.getvalue(), 'Ready. Press play to hear your translation.'
    except Exception:
        return translated, None, 'Translation ready. Audio service unavailable; please try again.'

def swap_languages(source, target, message, translation):
    if source not in LANGUAGES or target not in LANGUAGES:
        gr.Warning('Select Your language before swapping.')
        return (gr.skip(),) * 6
    return target, source, translation or '', message or '', None, ''


# UI translations are local, so changing the page language uses no service quota.
UI = {
    'en': ['Your words. A world of languages.', 'Choose your language and a destination language. Type your message, select Translate, then press play to listen.', 'Your language', 'To', 'Swap', 'Your message', 'Type or paste text here...', 'Read slowly', 'Translate & create audio', 'Translation', 'Listen to your translation', 'Clear', 'Text is sent to Google for translation and speech. Avoid sensitive information. Audio availability varies by language.', 'Ready. Press play to hear your translation.', 'Translation ready. Audio is unavailable for this language.', 'Translation ready. Audio service unavailable; please try again.', 'Enter some text to translate.', 'Please use 3,000 characters or fewer.', 'Translation could not complete. Check your connection or try again later.', 'Select both the input and translation languages.'],
    'hmn': ['Koj cov lus. Ntau hom lus thoob ntiaj teb.', 'Xaiv koj hom lus thiab hom lus uas koj xav txhais rau. Sau koj cov lus, nias Txhais lus, ces nias lub pob mloog.', 'Koj hom lus', 'Txhais rau', 'Hloov', 'Koj cov lus', 'Sau lossis muab koj cov lus tso ntawm no...', 'Nyeem qeeb', 'Txhais lus thiab tsim suab', 'Cov lus txhais', 'Mloog cov lus txhais', 'Lwv', 'Cov lus raug xa mus rau Google kom txhais thiab Google kom tsim suab. Tsis txhob sau tej ntaub ntawv ntiag tug. Qee hom lus tsis muaj suab.', 'Tiav lawm. Nias lub pob mloog kom hnov cov lus txhais.', 'Txhais tiav lawm. Hom lus no tsis muaj suab.', 'Txhais tiav lawm. Tsim tsis tau suab; thov sim dua.', 'Thov sau cov lus uas koj xav txhais.', 'Thov siv tsis tshaj 3,000 tus tsiaj ntawv.', 'Txhais tsis tau. Xyuas koj qhov internet lossis sim dua tom qab.', 'Thov xaiv ob hom lus.'],
    'es': ['Tus palabras. Un mundo de idiomas.', 'Elige tu idioma y el idioma de destino. Escribe tu mensaje, pulsa Traducir y luego reproduce el audio.', 'Tu idioma', 'Traducir a', 'Cambiar', 'Tu mensaje', 'Escribe o pega el texto aquí...', 'Leer despacio', 'Traducir y crear audio', 'Traducción', 'Escucha tu traducción', 'Borrar', 'El texto se envía a Google para traducir y a Google para generar voz. Evita información confidencial. El audio depende del idioma.', 'Listo. Pulsa reproducir para escuchar la traducción.', 'Traducción lista. No hay audio para este idioma.', 'Traducción lista. El servicio de audio no está disponible; inténtalo de nuevo.', 'Escribe un texto para traducir.', 'Usa un máximo de 3.000 caracteres.', 'No se pudo traducir. Revisa tu conexión o inténtalo más tarde.', 'Selecciona ambos idiomas.'],
    'fr': ['Vos mots. Un monde de langues.', 'Choisissez votre langue et la langue de destination. Saisissez votre message, cliquez sur Traduire, puis lancez la lecture audio.', 'Votre langue', 'Traduire en', 'Inverser', 'Votre message', 'Saisissez ou collez le texte ici...', 'Lire lentement', 'Traduire et créer le son', 'Traduction', 'Écoutez votre traduction', 'Effacer', 'Le texte est envoyé à Google pour la traduction et à Google pour la voix. Évitez les informations sensibles. Le son dépend de la langue.', 'Prêt. Lancez la lecture pour écouter la traduction.', 'Traduction prête. Le son est indisponible pour cette langue.', 'Traduction prête. Le service audio est indisponible ; réessayez.', 'Saisissez un texte à traduire.', 'Utilisez au maximum 3 000 caractères.', 'La traduction a échoué. Vérifiez votre connexion ou réessayez plus tard.', 'Sélectionnez les deux langues.'],
}
UI.update({
    'lo': ['ຄຳເວົ້າຂອງທ່ານ. ໂລກແຫ່ງພາສາ.', 'ເລືອກພາສາຂອງທ່ານ ແລະ ພາສາທີ່ຕ້ອງການແປ. ພິມຂໍ້ຄວາມ, ກົດແປ ແລ້ວກົດຫຼິ້ນເພື່ອຟັງ.', 'ພາສາຂອງທ່ານ', 'ແປເປັນ', 'ສະຫຼັບ', 'ຂໍ້ຄວາມຂອງທ່ານ', 'ພິມ ຫຼື ວາງຂໍ້ຄວາມຢູ່ນີ້...', 'ອ່ານຊ້າໆ', 'ແປ ແລະ ສ້າງສຽງ', 'ຄຳແປ', 'ຟັງຄຳແປຂອງທ່ານ', 'ລ້າງ', 'ຂໍ້ຄວາມຖືກສົ່ງໄປ Google ເພື່ອແປ ແລະ Google ເພື່ອສ້າງສຽງ. ຫຼີກລ້ຽງຂໍ້ມູນສ່ວນຕົວ. ບາງພາສາບໍ່ມີສຽງ.', 'ພ້ອມແລ້ວ. ກົດຫຼິ້ນເພື່ອຟັງຄຳແປ.', 'ແປແລ້ວ. ພາສານີ້ບໍ່ມີສຽງ.', 'ແປແລ້ວ. ບໍລິການສຽງບໍ່ພ້ອມ; ກະລຸນາລອງໃໝ່.', 'ກະລຸນາປ້ອນຂໍ້ຄວາມທີ່ຕ້ອງການແປ.', 'ກະລຸນາໃຊ້ບໍ່ເກີນ 3,000 ຕົວອັກສອນ.', 'ແປບໍ່ສຳເລັດ. ກວດສອບອິນເຕີເນັດ ຫຼື ລອງໃໝ່ພາຍຫຼັງ.', 'ກະລຸນາເລືອກທັງສອງພາສາ.'],
    'th': ['คำพูดของคุณ โลกแห่งภาษา', 'เลือกภาษาของคุณและภาษาที่ต้องการแปล พิมพ์ข้อความ กดแปล แล้วกดเล่นเพื่อฟัง', 'ภาษาของคุณ', 'แปลเป็น', 'สลับ', 'ข้อความของคุณ', 'พิมพ์หรือวางข้อความที่นี่...', 'อ่านช้า ๆ', 'แปลและสร้างเสียง', 'คำแปล', 'ฟังคำแปลของคุณ', 'ล้าง', 'ข้อความจะถูกส่งไปยัง Google เพื่อแปล และ Google เพื่อสร้างเสียง หลีกเลี่ยงข้อมูลที่ละเอียดอ่อน เสียงอาจไม่รองรับบางภาษา', 'พร้อมแล้ว กดเล่นเพื่อฟังคำแปล', 'แปลแล้ว ไม่มีเสียงสำหรับภาษานี้', 'แปลแล้ว บริการเสียงไม่พร้อมใช้งาน โปรดลองอีกครั้ง', 'กรุณาป้อนข้อความที่ต้องการแปล', 'กรุณาใช้ไม่เกิน 3,000 ตัวอักษร', 'แปลไม่สำเร็จ ตรวจสอบการเชื่อมต่อหรือลองอีกครั้งภายหลัง', 'กรุณาเลือกทั้งสองภาษา'],
    'zh': ['你的话语，世界的语言。', '选择你的语言和目标语言。输入文字，点击翻译，然后点击播放收听。', '你的语言', '翻译为', '交换', '你的文字', '在此输入或粘贴文字...', '慢速朗读', '翻译并生成语音', '译文', '收听译文', '清除', '文字会发送至 Google 进行翻译，并发送至 Google 生成语音。请勿输入敏感信息。部分语言不支持语音。', '已准备好。点击播放收听译文。', '翻译完成。此语言暂不支持语音。', '翻译完成。语音服务暂不可用，请重试。', '请输入需要翻译的文字。', '请使用不超过 3,000 个字符。', '翻译失败。请检查网络连接或稍后重试。', '请选择源语言和目标语言。'],
    'vi': ['Lời của bạn. Thế giới ngôn ngữ.', 'Chọn ngôn ngữ của bạn và ngôn ngữ đích. Nhập nội dung, nhấn Dịch, rồi nhấn phát để nghe.', 'Ngôn ngữ của bạn', 'Dịch sang', 'Đổi', 'Nội dung của bạn', 'Nhập hoặc dán văn bản vào đây...', 'Đọc chậm', 'Dịch và tạo âm thanh', 'Bản dịch', 'Nghe bản dịch', 'Xóa', 'Văn bản được gửi đến Google để dịch và Google để tạo giọng nói. Tránh nhập thông tin nhạy cảm. Một số ngôn ngữ không có âm thanh.', 'Đã sẵn sàng. Nhấn phát để nghe bản dịch.', 'Đã dịch. Ngôn ngữ này chưa có âm thanh.', 'Đã dịch. Dịch vụ âm thanh chưa khả dụng; vui lòng thử lại.', 'Vui lòng nhập văn bản cần dịch.', 'Vui lòng nhập tối đa 3.000 ký tự.', 'Không thể dịch. Hãy kiểm tra kết nối hoặc thử lại sau.', 'Vui lòng chọn cả hai ngôn ngữ.'],
})
PAGE_LANGUAGES = [('English', 'en'), ('Hmoob (Hmong)', 'hmn'), ('Español', 'es'), ('Français', 'fr'), ('ລາວ (Lao)', 'lo'), ('ไทย', 'th'), ('中文（简体）', 'zh'), ('Tiếng Việt', 'vi')]
NAMES = {
    'en': {'hmong': 'Hmong', 'english': 'English', 'spanish': 'Spanish', 'french': 'French'},
    'hmn': {'hmong': 'Hmoob', 'english': 'Lus Askiv', 'spanish': 'Lus Mev', 'french': 'Lus Fab Kis'},
    'es': {'hmong': 'Hmong', 'english': 'Inglés', 'spanish': 'Español', 'french': 'Francés'},
    'fr': {'hmong': 'Hmong', 'english': 'Anglais', 'spanish': 'Espagnol', 'french': 'Français'},
}

NAMES.update({
    'lo': dict(zip(['hmong','english','spanish','french','lao','thai','chinese (simplified)','chinese (traditional)','vietnamese'], ['ມົ້ງ','ອັງກິດ','ແອສປາໂຍນ','ຝຣັ່ງ','ລາວ','ໄທ','ຈີນ (ຕົວຫຍໍ້)','ຈີນ (ຕົວເຕັມ)','ຫວຽດນາມ'])),
    'th': dict(zip(['hmong','english','spanish','french','lao','thai','chinese (simplified)','chinese (traditional)','vietnamese'], ['ม้ง','อังกฤษ','สเปน','ฝรั่งเศส','ลาว','ไทย','จีน (ตัวย่อ)','จีน (ตัวเต็ม)','เวียดนาม'])),
    'zh': dict(zip(['hmong','english','spanish','french','lao','thai','chinese (simplified)','chinese (traditional)','vietnamese'], ['苗语','英语','西班牙语','法语','老挝语','泰语','中文（简体）','中文（繁体）','越南语'])),
    'vi': dict(zip(['hmong','english','spanish','french','lao','thai','chinese (simplified)','chinese (traditional)','vietnamese'], ['Tiếng Hmông','Tiếng Anh','Tiếng Tây Ban Nha','Tiếng Pháp','Tiếng Lào','Tiếng Thái','Tiếng Trung (Giản thể)','Tiếng Trung (Phồn thể)','Tiếng Việt'])),
})

def language_choices(locale):
    return [(NAMES[locale].get(name, name.title()), name) for name in sorted(LANGUAGES)]

def heading(locale):
    t = UI[locale]
    return f'# World Voice\n### {t[0]}\n{t[1]}'

def change_page_language(locale):
    t = UI[locale]
    return (heading(locale), gr.update(label=t[2], choices=language_choices(locale)),
            gr.update(label=t[3], choices=language_choices(locale)), gr.update(value=t[4]),
            gr.update(label=t[5], placeholder=t[6]), gr.update(label=t[7]),
            gr.update(value=t[8]), gr.update(label=t[9]), gr.update(label=t[10]),
            gr.update(value=t[11]), t[12], '')

PRONUNCIATION_UI = {
    'en': ('Pronunciation guide', 'Phonetic guide unavailable for this text or language.', 'Approximate guide; use the audio to hear pronunciation.'),
    'hmn': ('Kev nyeem cov lus', 'Tsis muaj lus qhia nyeem rau cov lus lossis hom lus no.', 'Lus qhia kwv yees; siv lub suab kom hnov kev nyeem.'),
    'es': ('Guía de pronunciación', 'No hay guía fonética para este texto o idioma.', 'Guía aproximada; escucha el audio para oír la pronunciación.'),
    'fr': ('Guide de prononciation', 'Guide phonétique indisponible pour ce texte ou cette langue.', 'Guide approximatif ; écoutez le son pour entendre la prononciation.'),
    'lo': ('ຄູ່ມືການອອກສຽງ', 'ບໍ່ມີຄູ່ມືການອອກສຽງສຳລັບຂໍ້ຄວາມ ຫຼື ພາສານີ້.', 'ຄູ່ມືໂດຍປະມານ; ຟັງສຽງເພື່ອຮຽນການອອກສຽງ.'),
    'th': ('คำอ่าน', 'ไม่มีคำอ่านสำหรับข้อความหรือภาษานี้', 'คำอ่านโดยประมาณ ใช้เสียงเพื่อฟังการออกเสียง'),
    'zh': ('发音指南', '此文字或语言暂无发音指南。', '仅供参考，请播放语音听取发音。'),
    'vi': ('Hướng dẫn phát âm', 'Chưa có phiên âm cho văn bản hoặc ngôn ngữ này.', 'Hướng dẫn gần đúng; hãy nghe âm thanh để biết cách phát âm.'),
}

@lru_cache(maxsize=128)
def phonetics(text, language):
    if language == 'english':
        import eng_to_ipa as ipa
        value = ipa.convert(text)
        # Unknown dictionary words are marked with an asterisk; don't invent sounds.
        if '*' in value or not value.strip():
            return ''
        return 'IPA: /' + value + '/'
    if language in ('chinese (simplified)', 'chinese (traditional)'):
        if not any('\u3400' <= c <= '\u9fff' for c in text):
            return ''
        from pypinyin import lazy_pinyin, Style
        return 'Pinyin: ' + ' '.join(lazy_pinyin(text, style=Style.TONE))
    return ''

def pronunciation_guide(text, language, locale):
    label, unavailable, note = PRONUNCIATION_UI[locale]
    if not text:
        return ''
    try:
        guide = phonetics(text, language)
    except Exception:
        guide = ''
    body = f'{html.escape(guide)}\n\n{note}' if guide else unavailable
    return f'**{label}**\n\n{body}'

def translate_with_pronunciation(text, source, target, slow, locale):
    translated, sound, status = localized_translate(text, source, target, slow, locale)
    return translated, sound, status, pronunciation_guide(translated, target, locale)

def swap_with_pronunciation(source, target, message, translation, locale):
    values = swap_languages(source, target, message, translation)
    if source not in LANGUAGES or target not in LANGUAGES:
        return (*values, gr.skip())
    return (*values, pronunciation_guide(message, source, locale))

def localized_translate(text, source, target, slow, locale):
    t = UI[locale]
    if not (text or '').strip():
        return '', None, t[16]
    if len(text) > 3000:
        return '', None, t[17]
    if source not in LANGUAGES or target not in LANGUAGES:
        return '', None, t[19]
    try:
        translated, sound, message = translate(text, source, target, slow)
    except gr.Error:
        return '', None, t[18]
    status_index = 13 if sound else (14 if 'this language' in message else 15)
    return translated, sound, t[status_index]

with gr.Blocks(title='World Voice | Translate & Listen', delete_cache=(3600,3600)) as demo:
    portrait_url = 'https://scontent.ffcm1-1.fna.fbcdn.net/v/t39.30808-6/753396728_27583441681305105_5910478644464753336_n.jpg?stp=cp6_dst-jpg_tt6&cstp=mx2047x2048&ctp=s2047x2048&_nc_cat=107&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=6ee11a&_nc_ohc=E5MqxKkaUkYQ7kNvwEKCn42&_nc_oc=Adq9oTGp6hFMXW0SblnE1ZzZXCESobNZuRlaQsP8P5ukhkqPrn7zjRMu_xADziyXvnmpYQM8sf4bOBli0gRs9XtR&_nc_zt=23&_nc_ht=scontent.ffcm1-1.fna&_nc_gid=b8UIftPMnPF2wYyjdwEQsg&_nc_ss=7b2a8&oh=00_AQOA7-2MbLvoAMIF5Mftf-H_OPe8MF63YQSvczt4_-QOSw&oe=6AD75B54'
    with gr.Row(elem_id='top-bar', equal_height=False):
        gr.HTML(f'<img src="{html.escape(portrait_url, quote=True)}" alt="World Voice creator portrait" style="display:block;width:180px;max-width:100%;height:auto;border-radius:18px;margin:0 0 2px;" referrerpolicy="no-referrer">', elem_id='creator-portrait', scale=4)
        page_language = gr.Dropdown(PAGE_LANGUAGES, value='en', label='🌐 Language / Hmoob / Idioma / Langue', scale=1, min_width=220, elem_id='page-language')
    intro = gr.Markdown(heading('en'))
    with gr.Row(elem_id='translation-languages'):
        source = gr.Dropdown(language_choices('en'), value=None, label=UI['en'][2])
        swap = gr.Button('Swap', scale=0, min_width=90)
        target = gr.Dropdown(language_choices('en'), value=None, label=UI['en'][3])
    text = gr.Textbox(label=UI['en'][5], placeholder=UI['en'][6], lines=6, max_length=3000)
    slow = gr.Checkbox(label=UI['en'][7])
    submit = gr.Button(UI['en'][8], variant='primary')
    result = gr.Textbox(label=UI['en'][9], lines=6, interactive=False)
    pronunciation = gr.Markdown()
    audio = gr.Audio(label=UI['en'][10], format='mp3', interactive=False)
    status = gr.Markdown()
    swap.click(swap_with_pronunciation, [source, target, text, result, page_language],
               [source, target, text, result, audio, status, pronunciation], queue=False)
    submit.click(translate_with_pronunciation, [text,source,target,slow,page_language], [result,audio,status,pronunciation], concurrency_limit=2)
    clear = gr.ClearButton([text,result,audio,status,pronunciation], value=UI['en'][11])
    privacy = gr.Markdown(UI['en'][12])
    page_language.change(change_page_language, page_language,
        [intro,source,target,swap,text,slow,submit,result,audio,clear,privacy,status], queue=False).then(
            pronunciation_guide, [result,target,page_language], pronunciation, queue=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--local', action='store_true')
    args = parser.parse_args()
    mobile_css = """
    body, .gradio-container { background: #eef7ed !important; }
    .gradio-container { font-family: Arial, sans-serif !important; }
    .gradio-container input, .gradio-container button, .gradio-container select {
        font-family: Arial, sans-serif !important;
    }
    #top-bar { margin-bottom: 0 !important; align-items: flex-start !important; }
    #creator-portrait { margin: 0 !important; padding: 0 !important; }
    @media (max-width: 640px) {
        .gradio-container { width: 100% !important; padding: 12px !important; }
        #top-bar { flex-wrap: nowrap !important; gap: 10px !important; }
        #creator-portrait { flex: 0 1 100px !important; min-width: 0 !important; }
        #creator-portrait img { width: 100px !important; }
        #page-language { flex: 1 1 180px !important; min-width: 0 !important; }
        #translation-languages { flex-direction: column !important; gap: 10px !important; }
        #translation-languages > * { width: 100% !important; min-width: 0 !important; }
        .gradio-container input, .gradio-container textarea { font-size: 16px !important; }
        .gradio-container button { min-height: 44px; touch-action: manipulation; }
        .gradio-container h1 { font-size: 28px !important; line-height: 1.2 !important; }
        .gradio-container h3 { font-size: 20px !important; }
        .gradio-container textarea { min-height: 130px !important; }
        .gradio-container audio { max-width: 100%; }
        .gradio-container p, .gradio-container label { overflow-wrap: anywhere; }
    }
    """
    demo.queue(max_size=20).launch(
        share=not args.local and not os.environ.get('PORT'),
        server_name='0.0.0.0' if os.environ.get('PORT') else '127.0.0.1',
        server_port=int(os.environ.get('PORT', '7860')),
        theme=gr.themes.Soft(font=['Arial', 'sans-serif'], font_mono=['Consolas', 'monospace']),
        css=mobile_css)
