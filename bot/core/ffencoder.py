from re import findall 
from math import floor
from time import time
from os import path as ospath
from aiofiles import open as aiopen
from aiofiles.os import remove as aioremove, rename as aiorename
from shlex import split as ssplit
from asyncio import sleep as asleep, gather, create_subprocess_shell, create_task
from asyncio.subprocess import PIPE
import random

from bot import Var, bot_loop, ffpids_cache, LOGS
from .func_utils import mediainfo, convertBytes, convertTime, sendMessage, editMessage
from .reporter import rep

ffargs = {
    '1080': Var.FFCODE_1080,
    '720': Var.FFCODE_720,
    '480': Var.FFCODE_480,
}

class AnimeProgress:
    """Mobile-friendly anime progress bars (8-12 segments)"""
    STYLES = {
        # Shonen (8 segments)
        'jjk': lambda p: f"🟣 {'■'*int(p/12)}{'□'*(10-int(p/12))} {p}% Domain",
        'chainsaw': lambda p: f"🔴 {'⛓️'*int(p/12)}{' '*(10-int(p/12))} {p}% Rev!",
        'demonslayer': lambda p: f"🔥 {'卍'*int(p/12)}{' '*(10-int(p/12))} {p}% Kagura",
        'onepiece': lambda p: f"🏴‍☠️ {'💎'*int(p/12)}{' '*(10-int(p/12))} {p}% Luffy!",
        'naruto': lambda p: f"🌀 {'忍'*int(p/12)}{' '*(9-int(p/12))} {p}% Dattebayo",
        
        # Modern (8 segments)
        'sololeveling': lambda p: f"👑 {'♠'*int(p/12)}{'♣'*(10-int(p/12))} {p}% Monarch",
        'spyxfamily': lambda p: f"🕵️ {'✓'*int(p/12)}{' '*(10-int(p/12))} {p}% Spy!",
        'mha': lambda p: f"💥 {'!'*int(p/12)}{'.'*(11-int(p/12))} {p}% SMASH",
        'tokyorevengers': lambda p: f"🚬 {'💢'*int(p/12)}{' '*(10-int(p/12))} {p}% Leap",
        'aot': lambda p: f"⚔️ {'◼'*int(p/12)}{'◻'*(10-int(p/12))} {p}% Rumble",
        
        # Classic (6 segments)
        'dbz': lambda p: f"⚡ {'💢'*int(p/16)}{' '*(10-int(p/16))} {p}% POWER!",
        'bleach': lambda p: f"🗡️ {'卍'*int(p/16)}{' '*(10-int(p/16))} {p}% Bankai",
        'hunter': lambda p: f"✨ {'☁'*int(p/16)}{'🌀'*(10-int(p/16))} {p}% Nen",  # 2-3 swirls max
        'onepunch': lambda p: f"👊 {'💥'*int(p/16)}{' '*(10-int(p/16))} {p}% OK.",
        'deathnote': lambda p: f"📓 {'⌛'*int(p/16)}{' '*(10-int(p/16))} {p}% Note",
        
        # Cyberpunk/Seinen (8 segments)
        'cyberpunk': lambda p: f"⏣ {'▞'*int(p/12)}{'▚'*(10-int(p/12))} {p}% CHOOM",
        'berserk': lambda p: f"✠ {'血'*int(p/16)}{' '*(10-int(p/16))} {p}% Clang",
        'evangelion': lambda p: f"✝️ {'▰'*int(p/12)}{'▱'*(10-int(p/12))} {p}% Sync",
        'ghostshell': lambda p: f"📡 {'⌖'*int(p/12)}{' '*(10-int(p/12))} {p}% Hack",
        'trigun': lambda p: f"🔫 {'✳'*int(p/12)}{' '*(10-int(p/12))} {p}% $$60B",
        
        # Retro (6 segments)
        'cowboybebop': lambda p: f"🎵 {'♫'*int(p/16)}{' '*(10-int(p/16))} {p}% Cowboy",
        'akira': lambda p: f"🔴 {'㊗'*int(p/16)}{' '*(10-int(p/16))} {p}% Tetsuo!",
        'gundam': lambda p: f"⚙️ {'✧'*int(p/16)}{' '*(10-int(p/16))} {p}% Newtype",
        'sailormoon': lambda p: f"🌙 {'✨'*int(p/16)}{' '*(10-int(p/16))} {p}% Prism",
        'dragonball': lambda p: f"🐉 {'☄'*int(p/16)}{' '*(10-int(p/16))} {p}% Kame!",
        
        # Hybrid (8 segments)
        'jjk_chainsaw': lambda p: f"🟣🔴 {'■⛓️'*int(p/24)}{'  '*(10-int(p/24))} {p}% Domain",
        'demon_bleach': lambda p: f"🔥🗡️ {'卍卍'*int(p/24)}{'  '*(10-int(p/24))} {p}% Bankai",
        'cyber_bebop': lambda p: f"⏣🎵 {'▞♫'*int(p/24)}{'  '*(10-int(p/24))} {p}% Bebop",
        'retro_modern': lambda p: f"🌀✨ {'忍☁'*int(p/24)}{'  '*(10-int(p/24))} {p}% Mix",
        'ultimate': lambda p: f"💥👊 {'!💢'*int(p/24)}{'  '*(10-int(p/24))} {p}% MAX"
    }


    @classmethod
    def get_random_style(cls):
        """Get a random anime style key"""
        return random.choice(list(cls.STYLES.keys()))
    
    @classmethod
    def get_progress(cls, percent: float, style: str = None):
        """Generate progress bar in specified style"""
        style = style or cls.get_random_style()
        generator = cls.STYLES.get(style, cls.STYLES['jjk'])
        return generator(min(100, max(0, percent)))

class FFEncoder:
    def __init__(self, message, path, name, qual):
        self.__proc = None
        self.is_cancelled = False
        self.message = message
        self.__name = name
        self.__qual = qual
        self.dl_path = path
        self.__total_time = None
        self.out_path = ospath.join("encode", name)
        self.__prog_file = 'prog.txt'
        self.__start_time = time()
        self.__current_style = None

    async def progress(self):
        self.__total_time = await mediainfo(self.dl_path, get_duration=True)
        if isinstance(self.__total_time, str):
            self.__total_time = 1.0
        
        # Select random style on first run
        if not self.__current_style:
            self.__current_style = AnimeProgress.get_random_style()
        
        while not (self.__proc is None or self.is_cancelled):
            async with aiopen(self.__prog_file, 'r+') as p:
                text = await p.read()
            
            if text:
                time_done = floor(int(t[-1]) / 1000000) if (t := findall("out_time_ms=(\d+)", text)) else 1
                ensize = int(s[-1]) if (s := findall(r"total_size=(\d+)", text)) else 0
                
                diff = time() - self.__start_time
                speed = ensize / diff
                percent = round((time_done/self.__total_time)*100, 2)
                tsize = ensize / (max(percent, 0.01)/100)
                eta = (tsize-ensize)/max(speed, 0.01)
    
                progress_bar = AnimeProgress.get_progress(percent, self.__current_style)
                
                progress_str = f"""<blockquote>‣ <b>Anime Name :</b> <b><i>{self.__name}</i></b></blockquote>
<blockquote>‣ <b>Status :</b> <i>Encoding</i>
    {progress_bar}</blockquote> 
<blockquote>   ‣ <b>Size :</b> {convertBytes(ensize)} out of ~ {convertBytes(tsize)}
    ‣ <b>Speed :</b> {convertBytes(speed)}/s
    ‣ <b>Time Took :</b> {convertTime(diff)}
    ‣ <b>Time Left :</b> {convertTime(eta)}</blockquote>
<blockquote>‣ <b>File(s) Encoded:</b> <code>{Var.QUALS.index(self.__qual)} / {len(Var.QUALS)}</code></blockquote>"""
            
                await editMessage(self.message, progress_str)
                if (prog := findall(r"progress=(\w+)", text)) and prog[-1] == 'end':
                    break
            await asleep(8)
    
    async def start_encode(self):
        if ospath.exists(self.__prog_file):
            await aioremove(self.__prog_file)
    
        async with aiopen(self.__prog_file, 'w+'):
            LOGS.info("Progress Temp Generated!")
            pass
        
        dl_npath, out_npath = ospath.join("encode", "ffanimeadvin.mkv"), ospath.join("encode", "ffanimeadvout.mkv")
        await aiorename(self.dl_path, dl_npath)
        
        ffcode = ffargs[self.__qual].format(dl_npath, self.__prog_file, out_npath)
        
        LOGS.info(f'FFCode: {ffcode}')
        self.__proc = await create_subprocess_shell(ffcode, stdout=PIPE, stderr=PIPE)
        proc_pid = self.__proc.pid
        ffpids_cache.append(proc_pid)
        _, return_code = await gather(create_task(self.progress()), self.__proc.wait())
        ffpids_cache.remove(proc_pid)
        
        await aiorename(dl_npath, self.dl_path)
        
        if self.is_cancelled:
            return
        
        if return_code == 0:
            if ospath.exists(out_npath):
                await aiorename(out_npath, self.out_path)
            return self.out_path
        else:
            await rep.report((await self.__proc.stderr.read()).decode().strip(), "error")
            
    async def cancel_encode(self):
        self.is_cancelled = True
        if self.__proc is not None:
            try:
                self.__proc.kill()
            except:
                pass
