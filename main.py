def create_long_video(topic, output_path="/tmp/final_video.mp4"):
    # استيراد متوافق مع كل الإصدارات
    try:
        from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
    except ImportError:
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

    scenes = [
        f"موضوع اليوم: {topic}",
        f"هل تعلم ان {topic} من اهم المواضيع التي يجب ان نعرفها؟",
        f"في البداية، {topic} يساعدنا على فهم الكثير من الامور المهمة حولنا.",
        f"ثانيا، هناك فوائد عديدة ل {topic} تجعل حياتنا افضل واكثر تنظيما.",
        f"ايضا، الكثير من الناس يجهلون اهمية {topic} وكيفية الاستفادة منه.",
        f"في الختام، نتمنى ان تكونوا استفدتم من هذا الفيديو عن {topic}، لا تنسوا الاشتراك.",
    ]

    clips = []
    for i, text in enumerate(scenes):
        audio_path = f"/tmp/audio_{i}.mp3"
        img_path = f"/tmp/img_{i}.jpg"
        asyncio.run(gen_audio(text, audio_path))
        create_image_with_text(text, i, img_path)
        audio_clip = AudioFileClip(audio_path)
        
        # إنشاء الصورة مع المدة
        image_clip = ImageClip(img_path, duration=audio_clip.duration + 0.4)
        
        # التوافق بين الإصدارين
        if hasattr(image_clip, 'with_audio'):
            image_clip = image_clip.with_audio(audio_clip)  # MoviePy 2.x
        else:
            image_clip = image_clip.set_audio(audio_clip)   # MoviePy 1.x
            
        clips.append(image_clip)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac', logger=None)
    return output_path
