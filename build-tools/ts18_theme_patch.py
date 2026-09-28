from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

root = Path("src")
assets = root / "theme/src/main/assets"
res = root / "theme/src/main/res"
mip = res / "mipmap-mdpi-v4"

manifest_path = root / "theme/src/main/AndroidManifest.xml"
manifest = manifest_path.read_text()
manifest = manifest.replace("sfp_cbk_black", "sfp_amap_kuwo")
manifest_path.write_text(manifest)

gradle_path = root / "theme/build.gradle.kts"
gradle = gradle_path.read_text()
gradle = gradle.replace(
    'applicationId = "launcher.variety.theme.plugin.sfp_cbk_black"',
    'applicationId = "launcher.variety.theme.plugin.sfp_amap_kuwo"'
)
gradle_path.write_text(gradle)

(res / "values/strings.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">TS18 Amap Kuwo Minimal</string>
    <string name="theme_name">TS18 Amap + Kuwo</string>
</resources>
""")

theme_config = {
    "source": "theme",
    "animation_type": "alpha",
    "background": "page_bg_01",
    "wallpaper_support": "false",
    "width": -1,
    "height": -1,
    "view_config_path": "home/view_config.json",
    "gravity": "l_0|t_0",
    "config": [{
        "page_bg": "",
        "apps_bg": "apps_bg_01",
        "page_config": [
            {
                "soft_type": "desktop_window",
                "width": 1144,
                "height": 583,
                "gravity": "l_81|t_119"
            },
            {
                "soft_type": "local_music|bt_music",
                "width": 860,
                "height": 64,
                "gravity": "l_81|t_55",
                "config_file_path": "media/media_config.json",
                "view_config_path": "media/media_view_config.json",
                "background": "media_bg"
            },
            {
                "soft_type": "time",
                "width": 284,
                "height": 64,
                "gravity": "l_941|t_55",
                "config_file_path": "time/time2_config.json",
                "view_config_path": "time/view2_config.json",
                "background": "time_bg"
            }
        ]
    }]
}
(assets / "theme_config.json").write_text(json.dumps(theme_config, ensure_ascii=False, indent=2))

hotseat = {
    "source": "theme",
    "width": 81,
    "height": 647,
    "image_path": "mipmap",
    "background": "",
    "gravity": "t_55|left",
    "config": [
        {
            "soft_type": "app", "width": 60, "height": 60,
            "gravity": "l_10|t_24", "use_app_widget": True,
            "view_config_path": "home/app_widget_view_config1.json",
            "background": "navi", "editable": True
        },
        {
            "soft_type": "app", "width": 60, "height": 60,
            "gravity": "l_10|t_124", "use_app_widget": True,
            "view_config_path": "home/app_widget_view_config1.json",
            "background": "music", "editable": True
        },
        {
            "soft_type": "app", "width": 60, "height": 60,
            "gravity": "l_10|t_224", "use_app_widget": True,
            "view_config_path": "home/app_widget_view_config1.json",
            "background": "bt", "editable": True
        },
        {
            "soft_type": "app", "width": 72, "height": 72,
            "gravity": "l_4|bottom|b_20", "use_app_widget": True,
            "view_config_path": "home/app_widget_view_config1.json",
            "background": "apps", "editable": False
        }
    ]
}
(assets / "hotseat_config.json").write_text(json.dumps(hotseat, ensure_ascii=False, indent=2))

media_path = assets / "media/media_config.json"
media = json.loads(media_path.read_text())
media["kw_music_head"] = "media_module_icon_kw"
media["media_layout_background"] = "media_bg"
media_path.write_text(json.dumps(media, ensure_ascii=False, indent=2))

media_view = {
    "source": "theme",
    "attributes": [
        {"id_name":"iv_media_icon","width":0,"height":0,"gravity":"center","visibility":False},
        {"id_name":"iv_media_icon_bg","width":0,"height":0,"gravity":"center","visibility":False},
        {"id_name":"tv_media_name","width":560,"height":-2,"gravity":"l_24|center_vertical","text_size":20,"text_color":"#F5F7FA","visibility":True,"is_shadow":False},
        {"id_name":"iv_media_head_img","width":0,"height":0,"visibility":False,"gravity":"left|top"},
        {"id_name":"tv_media_type","width":0,"height":0,"gravity":"center","visibility":False,"text_size":0,"text_color":"#FFFFFF","is_shadow":False},
        {"id_name":"iv_media_pre","width":56,"height":56,"gravity":"l_620|center_vertical"},
        {"id_name":"iv_media_pp","width":56,"height":56,"gravity":"l_692|center_vertical"},
        {"id_name":"iv_media_next","width":56,"height":56,"gravity":"l_764|center_vertical"},
        {"id_name":"iv_radio_icon","width":0,"height":0,"gravity":"center","visibility":False},
        {"id_name":"iv_radio_head_img","width":0,"height":0,"visibility":False,"gravity":"center"},
        {"id_name":"tv_radio_type","width":0,"height":0,"gravity":"center","visibility":False,"text_size":0,"text_color":"#FFFFFF"},
        {"id_name":"tv_radio_band","width":0,"height":0,"gravity":"center","visibility":False,"text_size":0,"text_color":"#FFFFFF"},
        {"id_name":"tv_radio_name","width":0,"height":0,"gravity":"center","visibility":False,"text_size":0,"text_color":"#FFFFFF"},
        {"id_name":"tv_radio_unit","width":0,"height":0,"visibility":False,"gravity":"center","text_size":0,"text_color":"#FFFFFF"},
        {"id_name":"iv_radio_pre","width":0,"height":0,"visibility":False,"gravity":"center"},
        {"id_name":"iv_radio_pp","width":0,"height":0,"visibility":False,"gravity":"center"},
        {"id_name":"iv_radio_next","width":0,"height":0,"visibility":False,"gravity":"center"}
    ]
}
(assets / "media/media_view_config.json").write_text(json.dumps(media_view, ensure_ascii=False, indent=2))

time_cfg = {
    "source":"local","image_path":"mipmap","background":"",
    "image_time_spacing":"time_spacing","format":"dd MMM",
    "visibility":True,"config_file_path":"time/view2_config",
    "use_system_am_pm":False,"use_system_week":False
}
(assets / "time/time2_config.json").write_text(json.dumps(time_cfg, ensure_ascii=False, indent=2))

time_view = {
    "source":"local",
    "attributes":[
        {"id_name":"tv_time_hour","width":116,"height":-2,"visibility":True,"text_size":27,"text_color":"#F5F7FA","gravity":"l_18|center_vertical"},
        {"id_name":"tv_time_day","width":124,"height":-2,"gravity":"right|r_18|center_vertical","text_size":18,"text_color":"#AEB7C2","visibility":True,"is_shadow":False},
        {"id_name":"tv_time_week","width":0,"height":0,"gravity":"center","text_size":0,"text_color":"#FFFFFF","visibility":False},
        {"id_name":"tv_ap","width":0,"height":0,"visibility":False,"text_size":0,"text_color":"#FFFFFF","gravity":"center"}
    ]
}
(assets / "time/view2_config.json").write_text(json.dumps(time_view, ensure_ascii=False, indent=2))

def rounded(size, fill, outline=None, radius=18):
    img = Image.new("RGBA", size, (0,0,0,0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((1,1,size[0]-2,size[1]-2), radius=radius, fill=fill, outline=outline, width=1)
    return img

bg = Image.new("RGB", (1280,720))
pix = bg.load()
for y in range(720):
    t = y / 719
    c = (int(10+5*t), int(14+7*t), int(19+10*t))
    for x in range(1280):
        pix[x,y] = c
bg.save(mip/"page_bg_01.png")
bg.save(mip/"apps_bg_01.png")

rounded((860,64),(20,25,32,242),(49,58,69,255),16).save(mip/"media_bg.png")
rounded((284,64),(20,25,32,242),(49,58,69,255),16).save(mip/"time_bg.png")
rounded((286,64),(20,25,32,242),(49,58,69,255),16).save(mip/"radio_bg.png")

def icon(kind, accent):
    im = Image.new("RGBA",(60,60),(0,0,0,0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((5,5,55,55),radius=15,fill=(22,28,36,245),outline=(55,66,78,255),width=1)
    if kind == "navi":
        d.polygon([(31,13),(44,45),(31,39),(20,47)],fill=accent)
        d.line((31,16,31,39),fill=(255,255,255,220),width=2)
    elif kind == "music":
        d.line((34,16,34,39),fill=accent,width=5)
        d.line((34,16,47,13),fill=accent,width=5)
        d.ellipse((21,35,35,49),fill=accent)
        d.ellipse((39,31,52,45),fill=accent)
    elif kind == "bt":
        d.line((30,13,30,47),fill=accent,width=4)
        d.line((30,13,43,25),fill=accent,width=4)
        d.line((43,25,30,36),fill=accent,width=4)
        d.line((30,24,18,15),fill=accent,width=4)
        d.line((30,36,18,45),fill=accent,width=4)
    else:
        for yy in (19,31,43):
            for xx in (19,31,43):
                d.rounded_rectangle((xx-3,yy-3,xx+3,yy+3),radius=2,fill=accent)
    return im

icon("navi",(63,211,198,255)).save(mip/"navi.png")
icon("music",(255,166,77,255)).save(mip/"music.png")
icon("bt",(126,167,255,255)).save(mip/"bt.png")
icon("apps",(224,229,236,255)).resize((72,72),Image.Resampling.LANCZOS).save(mip/"apps.png")

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font18 = ImageFont.truetype(font_path,18)
font22 = ImageFont.truetype(font_path,22)
font28 = ImageFont.truetype(bold_path,28)

for idx, night in [(1,False),(2,True)]:
    canvas = Image.new("RGB",(1280,720),(13,17,22) if night else (225,230,226))
    d = ImageDraw.Draw(canvas)
    d.rectangle((0,55,80,719), fill=(11,15,20))
    d.rounded_rectangle((81,55,939,118),radius=15,fill=(20,25,32))
    d.text((105,75),"KUWO  |  Now playing",font=font22,fill=(245,247,250))
    d.text((646,76),"<<     >     >>",font=font18,fill=(255,166,77))
    d.rounded_rectangle((941,55,1224,118),radius=15,fill=(20,25,32))
    d.text((970,70),"20:46",font=font28,fill=(245,247,250))
    d.text((1090,78),"28 SEP",font=font18,fill=(174,183,194))
    map_bg = (32,37,42) if night else (224,228,221)
    d.rectangle((81,119,1224,701),fill=map_bg)
    road = (95,103,110) if night else (255,255,255)
    minor = (62,69,75) if night else (202,207,200)
    for x in range(140,1200,150):
        d.line((x,130,x-100,690),fill=minor,width=3)
    for y in range(170,690,110):
        d.line((90,y,1210,y+45),fill=minor,width=3)
    d.line((100,600,500,420,850,450,1200,230),fill=road,width=14)
    d.line((100,600,500,420,850,450,1200,230),fill=(63,211,198),width=5)
    d.ellipse((612,378,636,402),fill=(63,211,198))
    d.text((98,137),"AMAP  /  NAVIGATION WINDOW",font=font18,fill=(50,210,195) if night else (25,115,105))
    for cy, ac in [(109,(63,211,198)),(209,(255,166,77)),(309,(126,167,255)),(654,(224,229,236))]:
        d.rounded_rectangle((10,cy-30,70,cy+30),radius=16,fill=(22,28,36),outline=(55,66,78))
        d.ellipse((35,cy-5,45,cy+5),fill=ac)
    canvas.save(mip/f"icon_local_theme_details_public_0{idx}.jpg",quality=92)

print("Patched TS18 Amap + Kuwo theme source")
