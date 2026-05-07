#!/usr/bin/env python3
import struct
import shutil
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

CHECKSUM_ADDRS = [
    0,0x90,0x120,0x1B0,0x240,0x2D0,0x4E0,0x570,
    0x37580,0x3B190,0x3B220,0x3B2B0,0x3B6C0,0x3B750,
    0x3DB60,0x3E770,0x40780,0x44F90,0x45020,0x450B0,
    0x45140,0x45250,0x45660,0x45770,0x56F80,0x56F90
]

BATTLE = 0x37590
OTHER  = 0x37D90
JEWEL  = 0x46380
MONEY  = 0x344B8
COMP   = 0x407B8
MEDAL  = 0x250
MIND1  = 0x360
MIND2  = 0x368
MIND3  = 0x370
MIND4  = 0x378
PLACE  = 0x4F0
NONE   = 0xFFFFFFFF

def u32(b,o): return struct.unpack_from('<I', b, o)[0]
def w32(b,o,v): struct.pack_into('<I', b, o, v & 0xFFFFFFFF)
def u16(b,o): return struct.unpack_from('<H', b, o)[0]
def w16(b,o,v): struct.pack_into('<H', b, o, v & 0xFFFF)

def checksum(buf, address, size):
    low = 0
    high = 1
    for i in range(size):
        value = buf[address+i]
        high = (value + 0x6c078965 * high) & 0xFFFFFFFF
        low = (low + (value + 1) * (i + 1) + 1) & 0xFFFFFFFF
    return ((high & 0xFFFF) << 16) | (low & 0xFFFF)

def fix_checksums(buf):
    for a, b in zip(CHECKSUM_ADDRS, CHECKSUM_ADDRS[1:]):
        if b <= len(buf):
            w32(buf, a, checksum(buf, a + 4, b - a - 4))

def add_or_set_item(buf, item_id, qty, base=OTHER, count=1024):
    for i in range(count):
        a = base + i * 8
        if a + 7 >= len(buf): break
        if u32(buf, a) == item_id:
            w32(buf, a, item_id)
            w16(buf, a + 4, qty)
            w16(buf, a + 6, 0)
            return "updated"
    for i in range(count):
        a = base + i * 8
        if a + 7 >= len(buf): break
        if u32(buf, a) == NONE and u16(buf, a + 4) == 0:
            w32(buf, a, item_id)
            w16(buf, a + 4, qty)
            w16(buf, a + 6, 0)
            return "added"
    return "full"

def get_item_qty(buf, item_id, base=OTHER, count=1024):
    for i in range(count):
        a = base + i * 8
        if a + 7 >= len(buf): break
        if u32(buf, a) == item_id:
            return u16(buf, a + 4)
    return 0

def remove_item(buf, item_id, base=OTHER, count=1024):
    for i in range(count):
        a = base + i * 8
        if a + 7 >= len(buf): break
        if u32(buf, a) == item_id:
            w32(buf, a, NONE)
            w16(buf, a + 4, 0)
            w16(buf, a + 6, 0)
            return True
    return False

def add_or_set_jewel(buf, jewel_id, qty=1):
    for i in range(120):
        a = JEWEL + i * 8
        if a + 7 >= len(buf): break
        if u32(buf, a + 4) == jewel_id:
            w16(buf, a, qty)
            w16(buf, a + 2, 0)
            return "updated"
    for i in range(120):
        a = JEWEL + i * 8
        if a + 7 >= len(buf): break
        jid = u32(buf, a + 4)
        q = u16(buf, a)
        if jid == NONE or q == 0:
            w16(buf, a, qty)
            w16(buf, a + 2, 0)
            w32(buf, a + 4, jewel_id)
            return "added"
    return "full"

def get_jewel_qty(buf, jewel_id):
    for i in range(120):
        a = JEWEL + i * 8
        if a + 7 >= len(buf): break
        if u32(buf, a + 4) == jewel_id:
            return u16(buf, a)
    return 0

def remove_jewel(buf, jewel_id):
    for i in range(120):
        a = JEWEL + i * 8
        if a + 7 >= len(buf): break
        if u32(buf, a + 4) == jewel_id:
            w16(buf, a, 0)
            w16(buf, a + 2, 0)
            w32(buf, a + 4, NONE)
            return True
    return False

BATTLE_ITEMS = [
    (0x0000,"Potion"),(0x0001,"Hi-Potion"),(0x0002,"X-Potion"),(0x0003,"Mega Potion"),
    (0x0004,"Ether"),(0x0005,"Hi-Ether"),(0x0006,"Turbo Ether"),(0x0007,"Mega-Ether"),
    (0x0008,"Phoenix Down"),(0x0009,"Phoenix Pinion"),(0x000A,"Mega Phoenix"),
    (0x000B,"Elixir"),(0x000C,"Megalixir"),(0x000D,"Antidote"),(0x000E,"Eye Drops"),
    (0x000F,"Rememb Herbs"),(0x0010,"Pick-Me-Up"),(0x0011,"Smelling Salt"),
    (0x0012,"Wobblestopper"),(0x0013,"Gold Hourglass"),(0x0014,"Tranquilizer"),
    (0x0015,"Remedy"),(0x0016,"Remedy+"),(0x0017,"Gysahl Greens"),
    (0x0018,"Bomb Fragment"),(0x0019,"Bomb Core"),(0x001A,"Fire Spellstone"),
    (0x001B,"Electro Marble"),(0x001C,"Lightning Marble"),(0x001D,"Lightning Spellstone"),
    (0x001E,"Figicite"),(0x001F,"Solid Figicite"),(0x0020,"Ice Spellstone"),
    (0x0021,"Fish Scale"),(0x0022,"Dragon Scale"),(0x0023,"Water Spellstone"),
    (0x0024,"Chimeric Wing"),(0x0025,"Dragon Wing"),(0x0026,"Wind Spellstone"),
    (0x0027,"Gaia Drum"),(0x0028,"Earth Hammer"),(0x0029,"Earth Spellstone"),
    (0x002E,"Protect Stone"),(0x002F,"Shell Stone"),(0x0030,"Haste Stone"),
    (0x0031,"Healing Spring"),(0x0032,"Star Curtain"),(0x0033,"Spider Silk"),
    (0x0034,"Holy Torch"),(0x0035,"Teleport Stone"),(0x0036,"Transfig Fruit"),
    (0x00BF,"Poison Fang"),(0x00C0,"Dream Powder"),(0x00C1,"Loco Weed"),
    (0x00C2,"Flash Bomb"),(0x00C3,"War Gong"),(0x00C4,"Lethean Chime"),
]

MISC_ITEMS = [
    (0x0037,"Semi-Lifetime Passes"),(0x0038,"Cornelian Letter"),(0x0039,"Warlock's Warmer"),
    (0x003A,"Magic Monocles"),(0x003B,"Key of Flames"),(0x003C,"Key of Earth"),
    (0x003D,"Key of Shadow"),(0x003E,"Key of Tides"),(0x003F,"Quacho Ruby"),
    (0x0040,"Poxyale"),(0x0041,"Antipoxy"),(0x0042,"Kyubi Souls"),
    (0x0077,"Arma Gem"),(0x0078,"Seraphone"),(0x0079,"Rename Prism"),
    (0x007A,"Rat Tail"),(0x007B,"Doga's Artifact"),(0x007C,"Griffin's Heart"),
    (0x007D,"Unei's Mirror"),(0x00D3,"Coliseum Ticket - Cactuar Johny"),
    (0x00D4,"Coliseum Ticket - White Chocobo"),(0x00D5,"Coliseum Ticket - Glow Moogle"),
    (0x00D6,"Coliseum Ticket - Red Bonnetberry"),(0x00D7,"Coliseum Ticket - Kobolt Mimic"),
    (0x00D8,"Coliseum Ticket - Dark Behemoth"),(0x00D9,"Coliseum Ticket - Sky Dragon"),
    (0x00DA,"Coliseum Ticket - Crimson Armor"),(0x00DB,"Coliseum Ticket - Topaz Carbuncle"),
    (0x00DC,"Coliseum Ticket - Kaguya Flan"),(0x00DD,"Coliseum Ticket - Iris"),
    (0x00DE,"Coliseum Ticket - Nidhogg"),(0x00DF,"Coliseum Ticket - Astraea"),
    (0x00E0,"Secret Memory"),(0x00E1,"Coliseum Ticket - Magitek Armor P"),
    (0x00E2,"Coliseum Ticket - Boko"),(0x00E3,"Coliseum Ticket - Miney"),
    (0x00E4,"Coliseum Ticket - Mo"),(0x00E5,"Coliseum Ticket - 2P Tama"),
    (0x00E6,"Coliseum Ticket - 2P Serafie"),
]

MEMENTOS = [
    (0x007E,"Ifrit Memento"),(0x007F,"Shiva Memento"),(0x0080,"Ramuh Memento"),
    (0x0081,"Adamantoise Memento"),(0x0082,"Hyperion Memento"),(0x0083,"Undead Princess Memento"),
    (0x0084,"Maduin Memento"),(0x0085,"Omega Memento"),(0x0086,"Ultima Weapon Memento"),
    (0x0087,"War Machine Memento"),(0x0088,"Einhander Memento"),(0x0089,"Cenchos Memento"),
    (0x008A,"Omega Bane Memento"),(0x008B,"Golem Head Memento"),(0x008C,"Mimic Queen Memento"),
    (0x008D,"Mecha Chocobo Memento"),(0x008E,"Princess Goblin Memento"),(0x008F,"Metalliskull Memento"),
    (0x0090,"Elefenrir Memento"),(0x0091,"Ultros Memento"),(0x0092,"Entom Soldier Memento"),
    (0x0093,"Valefor Memento"),(0x0094,"Nirvalefor Memento"),(0x0095,"Tamamohime Memento"),
    (0x0096,"Siren Memento"),(0x0097,"Diva Serafie Memento"),(0x0098,"Omega God Memento"),
    (0x0099,"Diabolos Memento"),(0x009A,"Leviathan Memento"),(0x009B,"Odin Memento"),
    (0x009C,"Shivalry Memento"),(0x009D,"Ifreeta Memento"),(0x009E,"Mist Dragon Memento"),
    (0x009F,"Nidhogg Memento"),(0x00A0,"Bismarck Memento"),(0x00A1,"Ultros Memento 2"),
    (0x00A2,"Black Chocochick Memento"),(0x00A3,"Cerberus Memento"),(0x00A4,"Glow Moogle Memento"),
    (0x00A5,"Kupicaroon Memento"),(0x00A6,"Iron Giant Memento"),(0x00A7,"Topaz Carbuncle Memento"),
    (0x00A8,"Elasmos Memento"),(0x00A9,"Kaguya Flan Memento"),(0x00AA,"Flan Princess Memento"),
    (0x00AB,"Malboro Menace Memento"),(0x00AC,"Sphinx Memento"),(0x00AD,"Phoenix Memento"),
    (0x00AE,"Holy Dragon Memento"),(0x00AF,"Titan Memento"),(0x00B0,"Fenrir Memento"),
    (0x00B1,"King Bomb Memento"),(0x00B2,"Vampire Prime Memento"),(0x00B3,"Asterius Memento"),
    (0x00B4,"Buer Memento"),(0x00B5,"Kraken Memento"),(0x00B6,"Tiamat Memento"),
    (0x00B7,"Tonberry King Memento"),(0x00B8,"Quacho Queen Memento"),(0x00B9,"Carbuncle Memento"),
    (0x00BA,"Ramewl Memento"),(0x00BB,"Kyubi Memento"),(0x00BC,"Elite Entom Memento"),
    (0x00BD,"Iron Muscles Memento"),(0x00BE,"Astraea Memento"),
    (0x00C5,"Weeglee Memento"),(0x00C6,"Gleed Memento"),(0x00C7,"Gleefrit Memento"),
    (0x00C8,"Brrblizz Memento"),(0x00C9,"Shivverina Memento"),(0x00CA,"Shivver Memento"),
    (0x00CB,"Joult Memento"),(0x00CC,"Voultr Memento"),(0x00CD,"Raiamuh Memento"),
    (0x00CE,"Nightmare Memento"),(0x00CF,"Magic Jar Memento"),(0x00D0,"Gigantuar Memento"),
    (0x00D1,"Gigantrot Memento"),(0x00D2,"Paleberry King Memento"),
]

PRISMS = [
    (0x010D,"Yurugu Prism"),(0x010E,"Fritt Prism"),(0x010F,"Weeglee Prism"),
    (0x0110,"Bablizz Prism"),(0x0111,"Brrblizz Prism"),(0x0112,"Zapt Prism"),
    (0x0113,"Joult Prism"),(0x0114,"Goblin Prism"),(0x0115,"Red Cap Prism"),
    (0x0116,"Chocochick Prism"),(0x0117,"Black Chocochick Prism"),(0x0118,"White Chocobo Prism"),
    (0x0119,"White Nakk Prism"),(0x011A,"Black Nakk Prism"),(0x011B,"Babyhemoth Prism"),
    (0x011C,"Kuza Kit Prism"),(0x011D,"Dark Behemoth Prism"),(0x011E,"Quacho Prism"),
    (0x011F,"Quachacho Prism"),(0x0120,"Moogle Prism"),(0x0121,"Glow Moogle Prism"),
    (0x0122,"Sharqual Prism"),(0x0123,"Nightsqual Prism"),(0x0124,"Red Bonnetberry Prism"),
    (0x0125,"Baby Tonberry Prism"),(0x0126,"Baby Paleberry Prism"),(0x0127,"Deathskull Prism"),
    (0x0128,"Mordskull Prism"),(0x0129,"Metalliskull Prism"),(0x012A,"Copper Gnome Prism"),
    (0x012B,"Lead Gnome Prism"),(0x012C,"Mu Prism"),(0x012D,"Reaver Mu Prism"),
    (0x012E,"Sea Snake Prism"),(0x012F,"Sea Serpent Prism"),(0x0130,"Minimantoise Prism"),
    (0x0131,"Flammantoise Prism"),(0x0132,"Brothetaur Prism"),(0x0133,"Sistertaur Prism"),
    (0x0134,"Water Toad Prism"),(0x0135,"Wind Toad Prism"),(0x0136,"Werebat Prism"),
    (0x0137,"Ice Bat Prism"),(0x0138,"Magic Pot Prism"),(0x0139,"Magic Jar Prism"),
    (0x013A,"Kobolt Mimic Prism"),(0x013B,"Sand Worm Prism"),(0x013C,"Sea Worm Prism"),
    (0x013D,"Right Claw Prism"),(0x013E,"Left Claw Prism"),(0x013F,"Bombino Prism"),
    (0x0140,"Mini Flan Prism"),(0x0141,"Kaguya Flan Prism"),(0x0142,"Mandragora Prism"),
    (0x0143,"Korrigan Prism"),(0x0144,"Manticore Prism"),(0x0145,"Sandicore Prism"),
    (0x0146,"Unicorn Prism"),(0x0147,"Nightmare Prism"),(0x0148,"Cockatrice Prism"),
    (0x0149,"Cocadrille Prism"),(0x014A,"Phoenix Prism"),(0x014B,"Iris Prism"),
    (0x014C,"Floating Eye Prism"),(0x014D,"Blood Eye Prism"),(0x014E,"Dualizard Prism"),
    (0x014F,"Bihydra Prism"),(0x0150,"Sylph Prism"),(0x0151,"Imp Prism"),
    (0x0152,"Garchimacera Prism"),(0x0153,"Mindflayer Prism"),(0x0154,"Squidraken Prism"),
    (0x0155,"Sky Dragon Prism"),(0x0156,"Spark Dragon Prism"),(0x0157,"Mist Dragon Prism"),
    (0x0158,"Mini Golem Prism"),(0x0159,"Water Golem Prism"),(0x015A,"Golem Head Prism"),
    (0x015B,"Cactuar Prism"),(0x015C,"Cactrot Prism"),(0x015D,"Cactuar Johnny Prism"),
    (0x015E,"Titan Prism"),(0x015F,"Iron Muscles Prism"),(0x0160,"Black Mage Prism"),
    (0x01BE,"Gilgamesh Prism"),(0x01E0,"Master Moogle Prism"),(0x01E1,"Master Cactuar Prism"),
    (0x01E2,"Master Tonberry Prism"),(0x01E3,"Master Chocochick Prism"),(0x01E4,"Mecha Chocobo Prism"),
    (0x01E5,"Boko Prism"),(0x01E6,"Ifrit Prism"),(0x01E7,"Ifreeta Prism"),
    (0x01E8,"Shiva Prism"),(0x01E9,"Shivalry Prism"),(0x01EA,"Ramuh Prism"),
    (0x01EB,"Ramewl Prism"),(0x01EC,"Leviathan Prism"),(0x01ED,"Bahamut Prism"),
    (0x01EE,"Odin Prism"),(0x01EF,"Diabolos Prism"),(0x01F0,"Quacho Queen Prism"),
    (0x01F1,"Miney Prism"),(0x01F2,"Mo Prism"),(0x01F3,"Princess Goblin Prism"),
    (0x01F4,"Ultros Prism"),(0x01F5,"Undead Princess Prism"),(0x01F6,"Kupicaroon Prism"),
    (0x01F7,"Topaz Carbuncle Prism"),(0x01F8,"Nidhogg Prism"),(0x01F9,"2P Tama Prism"),
    (0x01FA,"2P Serafie Prism"),
]

SEEDS = [(0x0209+i, name) for i, name in enumerate([
    "Fire Seed","Fira Seed","Firaga Seed","Blizzard Seed","Blizzara Seed","Blizzaga Seed",
    "Thunder Seed","Thundara Seed","Thundaga Seed","Water Seed","Watera Seed","Waterga Seed",
    "Aero Seed","Aerora Seed","Aeroga Seed","Quake Seed","Bio Seed","Drain Seed","Syphon Seed",
    "Death Seed","Meteor Seed","Flare Seed","Holy Seed","Ultima Seed","Cure Seed","Cura Seed",
    "Curaga Seed","Regen Seed","Esuna Seed","Raise Seed","Arise Seed","Protect Seed","Shell Seed",
    "Haste Seed","Slow Seed","Reflect Seed","Dispel Seed","Libra Seed","Berserk Seed","Bravery Seed",
    "Faith Seed","Balance Seed","Balancega Seed","Sleep Seed","Confuse Seed","Banish Seed",
    "Banishra Seed","Abyss Seed","HP+ Seed","HP++ Seed","HP+++ Seed","Strength+ Seed",
    "Strength++ Seed","Strength+++ Seed","Defence+ Seed","Defence++ Seed","Defence+++ Seed",
    "Magic+ Seed","Magic++ Seed","Magic+++ Seed","Magic Defence+ Seed","Magic Defence++ Seed",
    "Magic Defence+++ Seed","Agility+ Seed","Agility++ Seed","Agility+++ Seed","Accuracy+ Seed",
    "Accuracy++ Seed","Accuracy+++ Seed","Evasion+ Seed","Evasion++ Seed","Evasion+++ Seed",
    "Critical+ Seed","Critical++ Seed","Critical+++ Seed","Fire Resistance+ Seed",
    "Fire Resistance++ Seed","Fire Resistance+++ Seed","Ice Resistance+ Seed","Ice Resistance++ Seed",
    "Ice Resistance+++ Seed","Thunder Resistance+ Seed","Thunder Resistance++ Seed",
    "Thunder Resistance+++ Seed","Water Resistance+ Seed","Water Resistance++ Seed",
    "Water Resistance+++ Seed","Wind Resistance+ Seed","Wind Resistance++ Seed","Wind Resistance+++ Seed",
    "Earth Resistance+ Seed","Earth Resistance++ Seed","Earth Resistance+++ Seed","Light Resistance+ Seed",
    "Light Resistance++ Seed","Light Resistance+++ Seed","Dark Resistance+ Seed","Dark Resistance++ Seed",
    "Dark Resistance+++ Seed","All Resistance+ Seed","Resist Stun Seed","Resist Poison Seed",
    "Resist Sleep Seed","Resist Confusion Seed","Resist Blindness Seed","Resist Oblivion Seed",
    "Resist Berserk Seed","Resist Slow Seed","Resist Strength Down Seed","Resist Defence Down Seed",
    "Resist Magic Down Seed","Resist Magic Defence Down Seed","Resist Accuracy Down Seed",
    "Resist Evasion Down Seed","Safety Bit Seed","Stealth Seed","Vigilance Seed","First Strike Seed"
])]

MIRAJEWELS = [(i, name.replace(" Seed", " Mirajewel")) for i, name in enumerate([n for _, n in SEEDS] + ["Lure Seed","EXP Boost Seed","Gilfinder Seed","Treasure Hunter Seed"])]

# Champion Medal storage is 16 bytes / 128 possible bits, but only known medals are shown here.
# Bit order is based on the known save-editor flag layout.
CHAMPION_MEDALS = [
    (0, "Warrior of Light"),
    (1, "Refia"),
    (2, "Tifa"),
    (3, "Snow"),
    (4, "Lightning"),
    (5, "Squall"),
    (6, "Cloud"),
    (7, "Tidus"),
    (8, "Yuna"),
    (9, "Shantotto"),
    (10, "Terra"),
    (11, "Bartz"),
    (12, "Balthier"),
    (13, "Sephiroth"),
    (14, "Shelke"),
    (15, "Noctis"),
]

MIRAGE_NAME_BY_ID = {}
MIRAGE_ORDER_BY_MANUAL = ['Tama', 'Tamamohimé', 'Yurugu', 'Kyubi', '2P Tama', 'Chocochick', 'Chocobo', 'Mecha Chocobo', 'Black Chocochick', 'Hyperion', 'White Chocobo', 'Sylph', 'Siren', 'Serafie', 'Diva Serafie', '2P Serafie', 'Mu', 'Skull Eater', 'Carbuncle', 'Reaver Mu', 'Nut Eater', 'Topaz Carbuncle', 'Goblin', 'Goblin Guard', 'Princess Goblin', 'Red Cap', 'Red Captain', 'Mandragora', 'Malboro', 'Korrigan', 'Malboro Menace', 'Copper Gnome', 'Mythril Giant', 'Iron Giant', 'Lead Gnome', 'Chrome Giant', 'Mini Golem', 'Water Golem', 'Golem Head', 'Floating Eye', 'Ahriman', 'Blood Eye', 'Buer', 'Fritt', 'Affrite', 'Ifrit', 'Ifreeta', 'Weeglee', 'Gleed', 'Gleefrit', 'Bablizz', 'Mishiva', 'Shiva', 'Shivalry', 'Brrblizz', 'Shivverina', 'Shivver', 'Zapt', 'Zaphr', 'Ramuh', 'Ramewl', 'Joult', 'Voultr', 'Rairamuh', 'White Nakk', 'Fenrir', 'Cerberus', 'Black Nakk', 'Elefenrir', 'Babyhemoth', 'Behemoth', 'Behemonster', 'Kuza Kit', 'Kuza Beast', 'Dark Behemoth', 'Moogle', 'Kupirate', 'Kupicaroon', 'Glow Moogle', 'Deathskull', 'Undead Princess', 'Mordskull', 'Metalliskull', 'Right Claw', 'Left Claw', 'Cockatrice', 'Valefor', 'Cocadrille', 'Nirvalefor', 'Dualizard', 'Trihyde', 'Tiamat', 'Bihydra', 'Ghidra', 'Nidhogg', 'Cactuar', 'Gigantuar', 'Cactrot', 'Gigantrot', 'Cactuar Johnny', 'Magic Pot', 'Mimic', 'Mimic Queen', 'Magic Jar', 'Mimic Jackpot', 'Kobold Mimic', 'Quacho', 'Quacho Queen', 'Quachacho', 'Baby Tonberry', 'Tonberry', 'Tonberry King', 'Baby Paleberry', 'Paleberry', 'Paleberry King', 'Red Bonnetberry', 'Werebat', 'Vampire', 'Vampire Prime', 'Ice Bat', 'Demivampire', 'Mini Flan', 'Flan', 'Flan Princess', 'Kaguya Flan', 'Sharqual', 'Mega Sharqual', 'Bismarck', 'Nightsqual', 'Mega Nightsqual', 'Sea Snake', 'Leviathan', 'Sea Serpent', 'Elasmos', 'Minimantoise', 'Adamantoise', 'Flammantoise', 'Spark Dragon', 'Red Dragon', 'Mist Dragon', 'Holy Dragon', 'Sky Dragon', 'Bombino', 'Bomb', 'King Bomb', 'Phoenix', 'Iris', 'Water Toad', 'Lucky Toad', 'Wind Toad', 'Manticore', 'Sphinx', 'Sandicore', 'Memecoleous', 'Sand Worm', 'Sea Worm', 'Searcher', 'Magitek Armor', 'Death Machine', 'Security Eye', 'Magitek Armor A', 'War Machine', 'Death Searcher', 'Magitek Armor P', 'Crimson Armor', 'Imp', 'Diabolos', 'Garchimacera', 'Brothertaur', 'Minotaur', 'Sistertaur', 'Asterius', 'Gilgamesh', 'Unicorn', 'Odin', 'Nightmare', 'Mindflayer', 'Kraken', 'Ultros', 'Squidraken', 'Cenchos', 'Titan', 'Maduin', 'Iron Muscles', 'Magna Roader (Purple)', 'Magna Roader (Yellow)', 'Magna Roader (Red)', 'Entom Guard', 'Omega', 'Entom Soldier', 'Omega Bane', 'Elite Entom', 'Ultima Weapon', 'Supraltima Weapon', 'Einhänder', 'Astraea', 'XG', 'Omega God', 'Ifrit★', 'Shiva★', 'Ramuh★', 'Leviathan★', 'Bahamut★', 'Odin★', 'Diabolos★', 'Master Moogle', 'Master Cactuar', 'Master Tonberry', 'Mecha Chocobo★', 'Boko', 'Ifreeta★', 'Shivalry★', 'Ramewl★', 'Quacho Queen★', 'Miney', 'Mo', 'Princess Goblin★', 'Ultros★', 'Undead Princess★', 'Giant Goblin', 'Syldra', 'Grandfenrir', 'Mega Red Dragon', 'Golden Flan', 'Black Mage', 'Magitek Armor B', 'Bahamutian Soldier', 'Bahamutian Commander', 'Federation Guard', 'Mecha Choco', 'Ponini', 'Dramut', 'Sylphine', 'Devil Wolf', 'Lesser Coeurl', 'Moomba', 'Coeurl', 'Daigoro', 'Gamit', 'Yojimbo', 'Marilith', 'Lich', 'Largebuncle', 'Syldra★', 'Shiva-Ixion', 'Garland', 'Mel']


def read_bit(buf, bit_id):
    a = MEDAL + (bit_id // 8)
    mask = 1 << (bit_id % 8)
    if a >= len(buf):
        return False
    return (buf[a] & mask) != 0

def write_bit(buf, bit_id, value):
    a = MEDAL + (bit_id // 8)
    mask = 1 << (bit_id % 8)
    if a >= len(buf):
        return
    if value:
        buf[a] |= mask
    else:
        buf[a] &= (~mask) & 0xFF

class CategoryFrame(ttk.Frame):
    def __init__(self, parent, app, title, entries, base, count, default_qty=1, jewel=False):
        super().__init__(parent)
        self.app = app
        self.entries_all = entries
        self.entries = entries
        self.base = base
        self.count = count
        self.default_qty = default_qty
        self.jewel = jewel

        top = ttk.Frame(self)
        top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text=title).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.filter())
        ttk.Entry(top, textvariable=self.search_var).pack(side="right", fill="x", expand=True, padx=8)

        self.tree = ttk.Treeview(self, columns=("id","name","qty"), show="headings", selectmode="extended", height=18)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("qty", text="Owned")
        self.tree.column("id", width=90, stretch=False)
        self.tree.column("name", width=330)
        self.tree.column("qty", width=80, stretch=False)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        controls = ttk.Frame(self)
        controls.pack(fill="x", padx=6, pady=6)
        ttk.Label(controls, text="Quantity").pack(side="left")
        self.qty = tk.IntVar(value=default_qty)
        ttk.Spinbox(controls, from_=0, to=999, textvariable=self.qty, width=8).pack(side="left", padx=6)
        ttk.Button(controls, text="Add/update selected", command=self.add_selected).pack(side="left", padx=4)
        ttk.Button(controls, text="Remove selected", command=self.remove_selected).pack(side="left", padx=4)
        ttk.Button(controls, text="Add/update ALL in this tab", command=self.add_all).pack(side="left", padx=4)
        ttk.Button(controls, text="Refresh list", command=self.refresh).pack(side="right", padx=4)

        self.refresh()

    def filter(self):
        q = self.search_var.get().lower().strip()
        self.entries = [(i,n) for i,n in self.entries_all if q in n.lower() or q in f"{i:04X}".lower()]
        self.refresh()

    def get_owned(self, item_id):
        if self.app.buf is None:
            return ""
        if self.jewel:
            return get_jewel_qty(self.app.buf, item_id)
        return get_item_qty(self.app.buf, item_id, self.base, self.count)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for item_id, name in self.entries:
            self.tree.insert("", "end", iid=f"{item_id:X}", values=(f"{item_id:04X}", name, self.get_owned(item_id)))

    def selected_ids(self):
        return [int(iid, 16) for iid in self.tree.selection()]

    def add_selected(self):
        if not self.app.need(): return
        qty = max(0, int(self.qty.get()))
        ids = self.selected_ids()
        if not ids:
            messagebox.showinfo("No selection", "Select one or more entries first.")
            return
        self._set_ids(ids, qty)

    def add_all(self):
        if not self.app.need(): return
        qty = max(0, int(self.qty.get()))
        ids = [item_id for item_id, _ in self.entries_all]
        if not messagebox.askyesno("Add/update all", f"Add/update all {len(ids)} entries in this tab to quantity {qty}?"):
            return
        self._set_ids(ids, qty)

    def _set_ids(self, ids, qty):
        added = updated = full = 0
        for item_id in ids:
            if self.jewel:
                r = add_or_set_jewel(self.app.buf, item_id, qty)
            else:
                r = add_or_set_item(self.app.buf, item_id, qty, self.base, self.count)
            if r == "added": added += 1
            elif r == "updated": updated += 1
            else: full += 1
        self.app.status.set(f"Added {added}, updated {updated}, full/no-space {full}")
        self.app.refresh_summary()
        self.refresh()

    def remove_selected(self):
        if not self.app.need(): return
        ids = self.selected_ids()
        if not ids:
            messagebox.showinfo("No selection", "Select one or more entries first.")
            return
        removed = 0
        for item_id in ids:
            if self.jewel:
                if remove_jewel(self.app.buf, item_id): removed += 1
            else:
                if remove_item(self.app.buf, item_id, self.base, self.count): removed += 1
        self.app.status.set(f"Removed {removed} entries")
        self.app.refresh_summary()
        self.refresh()



def safe_icon_name(name):
    cleaned = "".join(c if c.isalnum() else "_" for c in name)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")

def find_mirage_icon(index, name):
    # Optional local icon support. Put PNGs beside this script in:
    # mirage_icons/001_Tama.png, 002_Tamamohime.png, etc.
    folder = Path(__file__).with_name("mirage_icons")
    if not folder.exists():
        return None
    candidates = [
        folder / f"{index+1:03d}_{safe_icon_name(name)}.png",
        folder / f"{index+1:03d}.png",
        folder / f"{safe_icon_name(name)}.png",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

class ChampionMedalFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        tk.Label(
            self,
            text="WARNING: Champion Medal editing is EXPERIMENTAL. Use backups before editing.",
            fg="red",
            font=("Segoe UI", 10, "bold")
        ).pack(fill="x", padx=8, pady=6)
        ttk.Label(self, text="Champion Medals (known named flags only; Sora excluded)").pack(fill="x", padx=8, pady=2)

        self.tree = ttk.Treeview(self, columns=("bit","name","owned"), show="headings", selectmode="extended", height=18)
        self.tree.heading("bit", text="Bit")
        self.tree.heading("name", text="Champion")
        self.tree.heading("owned", text="Owned")
        self.tree.column("bit", width=80, stretch=False)
        self.tree.column("name", width=360)
        self.tree.column("owned", width=100, stretch=False)
        self.tree.pack(fill="both", expand=True, padx=8, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=8, pady=6)
        ttk.Button(buttons, text="Unlock selected", command=self.unlock_selected).pack(side="left", padx=4)
        ttk.Button(buttons, text="Remove selected", command=self.remove_selected).pack(side="left", padx=4)
        ttk.Button(buttons, text="Unlock all known", command=self.unlock_all).pack(side="left", padx=4)
        ttk.Button(buttons, text="Refresh", command=self.refresh).pack(side="right", padx=4)

        ttk.Label(
            self,
            text="Note: the save has 128 possible bit slots, but this tab only shows known named medals. Champion Medals are stored as save flags. Use backups before editing."
        ).pack(fill="x", padx=8, pady=4)

        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for bit_id, name in CHAMPION_MEDALS:
            owned = ""
            if self.app.buf is not None:
                owned = "Yes" if read_bit(self.app.buf, bit_id) else "No"
            self.tree.insert("", "end", iid=str(bit_id), values=(bit_id, name, owned))

    def selected_bits(self):
        return [int(iid) for iid in self.tree.selection()]

    def unlock_selected(self):
        if not self.app.need(): return
        bits = self.selected_bits()
        for bit in bits:
            write_bit(self.app.buf, bit, True)
        self.app.status.set(f"Unlocked {len(bits)} selected Champion Medal flags")
        self.app.refresh_summary()
        self.refresh()

    def remove_selected(self):
        if not self.app.need(): return
        bits = self.selected_bits()
        for bit in bits:
            write_bit(self.app.buf, bit, False)
        self.app.status.set(f"Removed {len(bits)} selected Champion Medal flags")
        self.app.refresh_summary()
        self.refresh()

    def unlock_all(self):
        if not self.app.need(): return
        if not messagebox.askyesno("Unlock all known medals", "Unlock all known Champion Medals shown in this tab?"):
            return
        for bit, _ in CHAMPION_MEDALS:
            write_bit(self.app.buf, bit, True)
        self.app.status.set(f"Unlocked {len(CHAMPION_MEDALS)} known Champion Medal flags")
        self.app.refresh_summary()
        self.refresh()


class CompendiumFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        tk.Label(
            self,
            text="WARNING: Mirage Compendium editing is EXPERIMENTAL. Use selected entries only and keep backups.",
            fg="red",
            font=("Segoe UI", 10, "bold")
        ).pack(fill="x", padx=8, pady=6)
        self.rows = []
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())

        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="Mirage Compendium (experimental, selected entries only)").pack(side="left")
        ttk.Entry(top, textvariable=self.search_var).pack(side="right", fill="x", expand=True, padx=8)

        self.tree = ttk.Treeview(self, columns=("idx","id","name","seen","caught"), show="headings", selectmode="extended", height=18)
        self.tree.heading("idx", text="#")
        self.tree.heading("id", text="Mirage ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("seen", text="Seen")
        self.tree.heading("caught", text="Caught")
        self.tree.column("idx", width=60, stretch=False)
        self.tree.column("id", width=100, stretch=False)
        self.tree.column("name", width=300)
        self.tree.column("seen", width=80, stretch=False)
        self.tree.column("caught", width=80, stretch=False)
        self.tree.pack(fill="both", expand=True, padx=8, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=8, pady=6)
        ttk.Button(buttons, text="Set selected seen", command=self.set_seen).pack(side="left", padx=4)
        ttk.Button(buttons, text="Set selected caught", command=self.set_caught).pack(side="left", padx=4)
        ttk.Button(buttons, text="Clear selected flags", command=self.clear_selected).pack(side="left", padx=4)
        ttk.Button(buttons, text="Refresh", command=self.refresh).pack(side="right", padx=4)

        ttk.Label(
            self,
            text="Names are matched by Mirage Manual row order, while the internal save ID is still shown. If any row looks mismatched, use the internal ID as the source of truth."
        ).pack(fill="x", padx=8, pady=4)

        self.refresh()

    def load_rows(self):
        rows = []
        if self.app.buf is None:
            return rows
        for i in range(420):
            a = COMP + i * 0x14
            if a + 0x13 >= len(self.app.buf):
                break
            mid = u32(self.app.buf, a)
            if 0x1B58 <= mid <= 0x1FFF:
                flag = u32(self.app.buf, a+4)
                own = u32(self.app.buf, a+8)
                name = MIRAGE_ORDER_BY_MANUAL[i] if i < len(MIRAGE_ORDER_BY_MANUAL) else MIRAGE_NAME_BY_ID.get(mid, f"Mirage ID {mid:04X}")
                rows.append((i, mid, name, flag, own))
        return rows

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        q = self.search_var.get().lower().strip()
        for i, mid, name, flag, own in self.load_rows():
            if q and q not in name.lower() and q not in f"{mid:04X}".lower():
                continue
            seen = "Yes" if flag != 0 else "No"
            caught = "Yes" if flag >= 3 or own != 0 else "No"
            self.tree.insert("", "end", iid=str(i), values=(i, f"{mid:04X}", name, seen, caught))


    def on_select(self, event=None):
        if not hasattr(self, "icon_label"):
            return
        sel = self.tree.selection()
        if not sel:
            self.icon_label.configure(image="", text="No icon selected")
            self._current_icon = None
            return
        try:
            idx = int(sel[0])
        except Exception:
            return
        rows = {i: (mid, name, flag, own) for i, mid, name, flag, own in self.load_rows()}
        if idx not in rows:
            return
        mid, name, flag, own = rows[idx]
        path = find_mirage_icon(idx, name)
        if path and PIL_AVAILABLE:
            try:
                img = Image.open(path).convert("RGBA")
                img.thumbnail((96, 96))
                self._current_icon = ImageTk.PhotoImage(img)
                self.icon_label.configure(image=self._current_icon, text="")
                return
            except Exception:
                pass
        elif path:
            try:
                self._current_icon = tk.PhotoImage(file=str(path))
                self.icon_label.configure(image=self._current_icon, text="")
                return
            except Exception:
                pass
        self._current_icon = None
        self.icon_label.configure(image="", text=f"No local icon\\n{name}")

    def selected_indices(self):
        return [int(iid) for iid in self.tree.selection()]

    def set_seen(self):
        if not self.app.need(): return
        for i in self.selected_indices():
            a = COMP + i * 0x14
            w32(self.app.buf, a+4, 1)
        self.app.status.set("Selected compendium entries set to seen")
        self.app.refresh_summary()
        self.refresh()

    def set_caught(self):
        if not self.app.need(): return
        for i in self.selected_indices():
            a = COMP + i * 0x14
            w32(self.app.buf, a+4, 3)
            w32(self.app.buf, a+8, 1)
        self.app.status.set("Selected compendium entries set to caught")
        self.app.refresh_summary()
        self.refresh()

    def clear_selected(self):
        if not self.app.need(): return
        for i in self.selected_indices():
            a = COMP + i * 0x14
            for off in (4, 8, 12, 16):
                w32(self.app.buf, a+off, 0)
        self.app.status.set("Selected compendium flags cleared")
        self.app.refresh_summary()
        self.refresh()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WOFF Switch Save Editor")
        self.geometry("920x760")
        self.path = None
        self.buf = None
        self.status = tk.StringVar(value="Open a decrypted Switch gamedata file.")

        header = ttk.Frame(self)
        header.pack(fill="x", padx=8, pady=6)
        ttk.Button(header, text="Open gamedata", command=self.open).pack(side="left", padx=4)
        ttk.Button(header, text="Save As...", command=self.save_as).pack(side="left", padx=4)
        ttk.Button(header, text="Max Money", command=self.max_money).pack(side="left", padx=4)
        ttk.Label(header, textvariable=self.status).pack(side="left", padx=10)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)

        self.summary = tk.Text(self, height=10, wrap="word", font=("Consolas", 10))
        self.summary_frame = ttk.Frame(self.nb)
        self.summary.pack(in_=self.summary_frame, fill="both", expand=True, padx=8, pady=8)
        ttk.Button(self.summary_frame, text="Refresh summary", command=self.refresh_summary).pack(fill="x", padx=8, pady=5)
        self.nb.add(self.summary_frame, text="Summary")

        self.tabs = []
        self.add_category("Battle Items", BATTLE_ITEMS, BATTLE, 256, 99)
        self.add_category("Misc/Key Items", MISC_ITEMS, OTHER, 1024, 1)
        self.add_category("Prisms", PRISMS, OTHER, 1024, 1)
        self.add_category("Mementos", MEMENTOS, OTHER, 1024, 1)
        self.add_category("Seeds", SEEDS, OTHER, 1024, 99)
        self.add_category("Mirajewels", MIRAJEWELS, JEWEL, 120, 1, jewel=True)

        self.medal_tab = ChampionMedalFrame(self.nb, self)
        self.nb.add(self.medal_tab, text="Champion Medals (Experimental)")

        self.comp_tab = CompendiumFrame(self.nb, self)
        self.nb.add(self.comp_tab, text="Compendium (Experimental)")

        help_frame = ttk.Frame(self.nb)
        help_text = tk.Text(help_frame, height=20, wrap="word")
        help_text.pack(fill="both", expand=True, padx=8, pady=8)
        help_text.insert("1.0",
            "Safe workflow:\n"
            "1. Keep a JKSV backup before editing.\n"
            "2. Edit the raw gamedata file, not a ZIP archive.\n"
            "3. Save as a new gamedata file.\n"
            "4. Put the edited gamedata back into the original JKSV backup folder.\n\n"
            "Safe tabs:\n"
            "- Battle Items\n"
            "- Misc/Key Items\n"
            "- Prisms\n"
            "- Mementos\n"
            "- Seeds\n"
            "- Mirajewels\n"
            "- Champion Medals, known named bits only\n\n"
            "Experimental:\n"
            "- Mirage Compendium. Names are matched from the Mirage Manual order; internal IDs are still shown.\n"
        )
        help_text.configure(state="disabled")
        self.nb.add(help_frame, text="Help")

        exp = ttk.Frame(self.nb)
        tk.Label(exp, text="WARNING: Options on this tab are EXPERIMENTAL. Use backups before editing.", fg="red", font=("Segoe UI", 10, "bold")).pack(fill="x", padx=10, pady=10)
        ttk.Button(exp, text="Unlock all known Champion Medals", command=self.champion_medals).pack(fill="x", padx=10, pady=4)
        ttk.Button(exp, text="Unlock Mirage Compendium", command=self.comp).pack(fill="x", padx=10, pady=4)
        ttk.Button(exp, text="Rollback known risky edits / recovery", command=self.rollback_risky).pack(fill="x", padx=10, pady=12)
        self.nb.add(exp, text="Experimental")

    def add_category(self, title, entries, base, count, default_qty, jewel=False):
        frame = CategoryFrame(self.nb, self, title, entries, base, count, default_qty, jewel)
        self.tabs.append(frame)
        self.nb.add(frame, text=title)

    def need(self):
        if self.buf is None:
            messagebox.showerror("No save", "Open gamedata first.")
            return False
        return True

    def open(self):
        p = filedialog.askopenfilename(title="Open decrypted WOFF gamedata")
        if not p: return
        self.path = Path(p)
        self.buf = bytearray(self.path.read_bytes())
        self.status.set(f"Loaded {self.path.name} ({len(self.buf)} bytes)")
        self.refresh_summary()
        self.refresh_all_tabs()

    def save_as(self):
        if not self.need(): return
        p = filedialog.asksaveasfilename(title="Save edited gamedata as", initialfile="gamedata")
        if not p: return
        p = Path(p)
        if p.exists():
            backup = p.with_suffix(p.suffix + f".bak_{int(time.time())}")
            shutil.copy2(p, backup)
        fix_checksums(self.buf)
        p.write_bytes(self.buf)
        self.status.set(f"Saved {p}")
        messagebox.showinfo("Saved", "Saved edited gamedata. Restore with JKSV/Checkpoint.")

    def refresh_all_tabs(self):
        for tab in self.tabs:
            tab.refresh()
        if hasattr(self, "medal_tab"):
            self.medal_tab.refresh()
        if hasattr(self, "comp_tab"):
            self.comp_tab.refresh()

    def refresh_summary(self):
        if self.buf is None: return
        battle_count, battle_qty = self.count_existing(BATTLE, 256)
        other_count, other_qty = self.count_existing(OTHER, 1024)
        lines = [
            f"Money: {u32(self.buf, MONEY):,}",
            f"Battle item slots used: {battle_count}/256   total qty: {battle_qty}",
            f"Other/key item slots used: {other_count}/1024   total qty: {other_qty}",
            f"Arma Gems: {get_item_qty(self.buf, 0x77, OTHER, 1024)}",
            f"Seeds present: {sum(1 for i,_ in SEEDS if get_item_qty(self.buf,i,OTHER,1024)>0)}/{len(SEEDS)}",
            f"Prisms present: {sum(1 for i,_ in PRISMS if get_item_qty(self.buf,i,OTHER,1024)>0)}/{len(PRISMS)}",
            f"Mementos present: {sum(1 for i,_ in MEMENTOS if get_item_qty(self.buf,i,OTHER,1024)>0)}/{len(MEMENTOS)}",
            f"Mirajewels present: {sum(1 for i,_ in MIRAJEWELS if get_jewel_qty(self.buf,i)>0)}/{len(MIRAJEWELS)}",
            f"Champion Medal known flags set: {sum(1 for bit,_ in CHAMPION_MEDALS if read_bit(self.buf, bit))}/{len(CHAMPION_MEDALS)} known medals",
        ]
        self.summary.delete("1.0", "end")
        self.summary.insert("1.0", "\n".join(lines))
        self.refresh_all_tabs()

    def count_existing(self, base, count):
        used = total = 0
        for i in range(count):
            a = base + i * 8
            if a + 7 >= len(self.buf): break
            item = u32(self.buf,a)
            qty = u16(self.buf,a+4)
            if item != NONE and qty > 0:
                used += 1
                total += qty
        return used, total

    def max_money(self):
        if not self.need(): return
        w32(self.buf, MONEY, 9999999)
        self.status.set("Money maxed")
        self.refresh_summary()

    def champion_medals(self):
        if not self.need(): return
        if not messagebox.askyesno("Experimental", "Unlock Champion Medals is experimental. Continue only with a backup."):
            return
        for i in range(0x10):
            self.buf[MEDAL+i] = 0xFF
        self.status.set("Champion Medal flags unlocked")
        self.refresh_summary()

    def comp(self):
        if not self.need(): return
        if not messagebox.askyesno("Experimental Mirage Compendium", "This writes Mirage Compendium flags and may be unstable. Continue?"):
            return
        changed = 0
        for i in range(420):
            a = COMP + i * 0x14
            if a + 0x13 >= len(self.buf): break
            mid = u32(self.buf,a)
            if 0x1B58 <= mid <= 0x1FFF:
                w32(self.buf,a+4,3)
                w32(self.buf,a+8,1)
                changed += 1
        self.status.set(f"Compendium written: {changed} entries")
        self.refresh_summary()

    def rollback_risky(self):
        if not self.need(): return
        if not messagebox.askyesno("Rollback risky edits", "Clear Champion Medals, compendium flags, and Mirajewel table?"):
            return
        changed = 0
        for i in range(0x10):
            if self.buf[MEDAL+i] != 0:
                self.buf[MEDAL+i] = 0
                changed += 1
        for i in range(420):
            a = COMP + i * 0x14
            if a + 0x13 >= len(self.buf): break
            mid = u32(self.buf,a)
            if 0x1B58 <= mid <= 0x1FFF:
                for off in (4,8,12,16):
                    if u32(self.buf,a+off) != 0:
                        w32(self.buf,a+off,0)
                        changed += 1
        for i in range(120):
            a = JEWEL + i*8
            if u16(self.buf,a) != 0 or u32(self.buf,a+4) != NONE:
                w16(self.buf,a,0)
                w16(self.buf,a+2,0)
                w32(self.buf,a+4,NONE)
                changed += 1
        self.status.set(f"Rollback complete: cleared {changed}")
        self.refresh_summary()

if __name__ == "__main__":
    App().mainloop()
