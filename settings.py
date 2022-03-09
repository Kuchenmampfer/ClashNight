import asyncio
import coc
import asyncpg
import logging
from discord import Intents

import production_secrets
import daemon_secrets
import dev_secrets


class Settings:
    def __init__(self, dev_mode: bool, daemon: bool):
        if dev_mode:
            if daemon:
                self.coc_client = coc.login(dev_secrets.coc_dev_email, dev_secrets.coc_dev_password, coc.EventsClient,
                                            key_names=dev_secrets.coc_dev_key, throttle_limit=40)
                self.dsn = dev_secrets.postgres_dsn_str
                self.webhook_url = daemon_secrets.logging_webhook_url
                self.log_level = logging.DEBUG
            else:
                self.discord_bot_token = dev_secrets.discord_bot_token
                self.coc_client = coc.login(dev_secrets.coc_dev_email, dev_secrets.coc_dev_password, coc.EventsClient,
                                            key_names=dev_secrets.coc_dev_key, throttle_limit=30)
                self.dsn = dev_secrets.postgres_dsn_str
                self.webhook_url = dev_secrets.logging_webhook_url
                self.log_level = logging.DEBUG
                self.prefixes = {805155951324692571: ','}
                self.war_report_channel_id = dev_secrets.WAR_REPORT_CHANNEL_ID
        else:
            if daemon:
                self.coc_client = coc.login(daemon_secrets.coc_dev_email, daemon_secrets.coc_dev_password,
                                            coc.EventsClient, key_count=10, throttle_limit=20)
                self.dsn = daemon_secrets.postgres_dsn_str
                self.webhook_url = daemon_secrets.logging_webhook_url
                self.log_level = logging.INFO
            else:
                self.discord_bot_token = production_secrets.discord_bot_token
                self.coc_client = coc.login(production_secrets.coc_dev_email, production_secrets.coc_dev_password,
                                            coc.EventsClient,
                                            key_names=production_secrets.coc_dev_key, throttle_limit=20)
                self.dsn = production_secrets.postgres_dsn_str
                self.webhook_url = production_secrets.logging_webhook_url
                self.log_level = logging.INFO
                self.prefixes = {805155951324692571: '!'}
                self.war_report_channel_id = production_secrets.WAR_REPORT_CHANNEL_ID
        self.intents = Intents.all()
        self.cogs = initial_extensions
        self.emotes = emotes


initial_extensions = (
    "cogs.general",
    "cogs.Admin.db_events",
    "cogs.Admin.initialize_db",
    "cogs.Admin.run_stuff",
    "cogs.BuilderBase.my",
    "cogs.BuilderBase.profile",
    "cogs.BuilderBase.registration",
    "cogs.BuilderBase.leaderboards",
)

emotes = {
    'blank': '<:bl:821447803917697044>',
    '14': '<:14:828991721181806623>',
    '13': '<:132:704082689816395787>',
    '12': '<:12:701579365162418188>',
    '11': '<:11:701579365699551293>',
    '10': '<:10:701579365661671464>',
    '9': '<:09:701579365389041767>',
    '8': '<:08:701579365321801809>',
    '7': '<:07:701579365598756874>',
    '6': '<:06:701579365573459988>',
    '5': '<:05:701579365581848616>',
    '4': '<:04:701579365850284092>',
    '3': '<:03:701579364600643634>',
    '2': '<:02:701579364483203133>',
    '1': '<:01:701579364193534043>',
    'onestar': '<:onestar:817098559043928164>',
    'twostar': '<:twostar:817098559999705109>',
    'threestar': '<:threestar:817098559476072458>',
    'zerostar': '<:zerostar:817104090961412146>',
    3: '<:n3:821097470339579935>',
    6: '<:n6:821097470356094998>',
    4: '<:n4:821097470472749147>',
    5: '<:n5:821097470502371329>',
    1: '<:n1:821097470503288832>',
    7: '<:n7:821097470515871755>',
    2: '<:n2:821097470603952138>',
    13: '<:n13:821097470712479755>',
    8: '<:n8:821097470842372177>',
    10: '<:n10:821097470867669042>',
    9: '<:n9:821097470880514058>',
    11: '<:n11:821097470888509480>',
    19: '<:n19:821097470934384651>',
    12: '<:n12:821097470934515749>',
    23: '<:n23:821097470947229787>',
    15: '<:n15:821097470985109555>',
    17: '<:n17:821097471107268655>',
    18: '<:n18:821097471114739722>',
    14: '<:n14:821097471135580200>',
    16: '<:n16:821097471135711332>',
    21: '<:n21:821097471261540352>',
    20: '<:n20:821097471312003122>',
    22: '<:n22:821097471319998514>',
    24: '<:n24:821097471391301632>',
    25: '<:n25:821097471483969556>',
    26: '<:n26:821097471492882462>',
    28: '<:n28:821097472083886152>',
    30: '<:n30:821097472146931743>',
    41: '<:n41:821097472276693033>',
    27: '<:n27:821097472365559808>',
    44: '<:n44:821097472377094186>',
    29: '<:n29:821097472427425792>',
    34: '<:n34:821097472448790620>',
    38: '<:n38:821097472511574057>',
    35: '<:n35:821097472511967243>',
    50: '<:n50:821097472537264139>',
    32: '<:n32:821097472566231130>',
    47: '<:n47:821097472595329035>',
    33: '<:n33:821097472599261254>',
    40: '<:n40:821097472599785492>',
    36: '<:n36:821110194045583360>',
    43: '<:n43:821097472603455558>',
    46: '<:n46:821097472604110869>',
    42: '<:n42:821097472608174121>',
    37: '<:n37:821097472620232724>',
    48: '<:n48:821097472628621342>',
    39: '<:n39:821097472633471056>',
    45: '<:n45:821097472649855026>',
    49: '<:n49:821097472671744020>',
    31: '<:n31:821097472821690368>',
    53: '<:n53:821099561158180906>',
    51: '<:n51:821099561443131412>',
    52: '<:n52:821099561459122286>',
    59: '<:n59:821099561514827858>',
    54: '<:n54:821099561619685406>',
    55: '<:n55:821099561656516618>',
    56: '<:n56:821099561695051867>',
    57: '<:n57:821099561807380490>',
    66: '<:n66:821099561896247299>',
    58: '<:n58:821099561921544215>',
    62: '<:n62:821099561958637569>',
    61: '<:n61:821099561970958406>',
    60: '<:n60:821099561983672370>',
    70: '<:n70:821099562055106582>',
    67: '<:n67:821099562067558432>',
    64: '<:n64:821099562152099860>',
    65: '<:n65:821099562286317588>',
    68: '<:n68:821099562352902210>',
    63: '<:n63:821099562374004756>',
    69: '<:n69:821099562475323472>',
    71: '<:n71:821099562633789490>',
    78: '<:n78:821099563594678304>',
    79: '<:n79:821099563631902741>',
    76: '<:n76:821099563695079495>',
    74: '<:n74:821099563703205968>',
    90: '<:n90:821099563712512053>',
    73: '<:n73:821099563716837406>',
    75: '<:n75:821099563791286302>',
    81: '<:n81:821099563791548491>',
    93: '<:n93:821099563850137692>',
    80: '<:n80:821099563942543430>',
    95: '<:n95:821099564022890516>',
    86: '<:n86:821099564043206686>',
    87: '<:n87:821099564064702484>',
    94: '<:n94:821099564064964608>',
    88: '<:n88:821099564072304660>',
    92: '<:n92:821099564072435762>',
    85: '<:n85:821099564076630016>',
    82: '<:n82:821099564080693278>',
    77: '<:n77:821099564084887563>',
    97: '<:n97:821099564110970881>',
    83: '<:n83:821099564114771978>',
    89: '<:n89:821099564131549234>',
    72: '<:n72:821099564169166878>',
    91: '<:n91:821099564186075156>',
    99: '<:n99:821099564198920222>',
    96: '<:n96:821099564228280330>',
    84: '<:n84:821099564240863272>',
    98: '<:n98:821099564249120788>',
    100: '<:n100:821105330117017622>',
    101: '<:n101:821100621456343091>',
    104: '<:n104:821100621608386642>',
    102: '<:n102:821100621700661278>',
    103: '<:n103:821100621712850984>',
    105: '<:n105:821100621754007564>',
    106: '<:n106:821100621880098916>',
    107: '<:n107:821100621922173008>',
    108: '<:n108:821100621997932595>',
    121: '<:n121:821100622056259685>',
    109: '<:n109:821100622114717726>',
    120: '<:n120:821100622148665385>',
    113: '<:n113:821100622156922941>',
    111: '<:n111:821100622161772614>',
    112: '<:n112:821100622178025532>',
    110: '<:n110:821100622178418728>',
    115: '<:n115:821100622265974904>',
    117: '<:n117:821100622312112178>',
    114: '<:n114:821100622329675816>',
    118: '<:n118:821100622450786365>',
    116: '<:n116:821100622521958410>',
    119: '<:n119:821100622711226388>',
    122: '<:n122:821100622807957574>',
    125: '<:n125:821100623034318950>',
    126: '<:n126:821100623050571817>',
    127: '<:n127:821100623184789556>',
    123: '<:n123:821100623243640902>',
    148: '<:n148:821100623247573014>',
    130: '<:n130:821100623290040394>',
    134: '<:n134:821100623319662615>',
    124: '<:n124:821100623331983410>',
    132: '<:n132:821100623385591899>',
    144: '<:n144:821100623403548703>',
    147: '<:n147:821100623407218720>',
    128: '<:n128:821100623478915082>',
    141: '<:n141:821100623487434793>',
    136: '<:n136:821100623520595999>',
    129: '<:n129:821100623536717914>',
    131: '<:n131:821100623553757225>',
    133: '<:n133:821100623578660934>',
    137: '<:n137:821100623616802827>',
    143: '<:n143:821100623620472858>',
    138: '<:n138:821100623651012629>',
    145: '<:n145:821100623675523082>',
    150: '<:n150:821100623679979591>',
    135: '<:n135:823170635643617291>',
    140: '<:n140:821100623692562442>',
    139: '<:n139:821100623717072916>',
    146: '<:n146:821100623725461519>',
    142: '<:n142:821100623734374410>',
    149: '<:n149:821100623784312872>',
    151: '<:n151:821101157682249769>',
    152: '<:n152:821101158059081768>',
    154: '<:n154:821101158084771850>',
    155: '<:n155:821101158114132008>',
    153: '<:n153:821101158126714920>',
    156: '<:n156:821101158155943943>',
    160: '<:n160:821101158230654987>',
    157: '<:n157:821101158483230751>',
    158: '<:n158:823171077152440382>',
    159: '<:n159:821101158520193034>',
    162: '<:n162:821101158567116852>',
    165: '<:n165:821101158684033055>',
    163: '<:n163:821101158730956820>',
    168: '<:n168:821101158734102559>',
    164: '<:n164:821101158789414932>',
    166: '<:n166:821101158810255401>',
    167: '<:n167:821101158876708884>',
    173: '<:n173:821101158911311953>',
    161: '<:n161:821101158969507961>',
    171: '<:n171:821101159011188787>',
    169: '<:n169:821101159027703888>',
    170: '<:n170:821101159099924490>',
    172: '<:n172:821101159154188368>',
    182: '<:n182:821101159565623317>',
    175: '<:n175:821101159657635900>',
    176: '<:n176:821101159745716224>',
    180: '<:n180:821101159808237648>',
    199: '<:n199:821101159838253087>',
    178: '<:n178:821101159862894642>',
    177: '<:n177:821101159900512306>',
    196: '<:n196:821101159900643329>',
    179: '<:n179:821101159942324255>',
    183: '<:n183:821101159962902558>',
    174: '<:n174:821101160006025236>',
    190: '<:n190:821101160047050823>',
    187: '<:n187:821101160063565854>',
    181: '<:n181:821101160094105600>',
    188: '<:n188:821101160098299976>',
    195: '<:n195:821101160127397919>',
    185: '<:n185:821101160155971612>',
    200: '<:n200:821101160194375761>',
    184: '<:n184:821101160236580864>',
    189: '<:n189:821101160239988787>',
    193: '<:n193:821101160248639518>',
    192: '<:n192:821101160286388244>',
    194: '<:n194:821101160299364372>',
    186: '<:n186:821101160337113092>',
    197: '<:n197:821101160470413322>',
    198: '<:n198:821101160482996224>',
    191: '<:n191:821101160701755452>',
    'pinkphallicobject': '<:pinkphallicobject:821877908163264522>',
}
