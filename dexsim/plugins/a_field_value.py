import logging
import os
import re

import yaml
from smaliemu.emulator import Emulator

from ..plugin import Plugin

__all__ = ["FieldValue"]

logger = logging.getLogger(__name__)


class FieldValue(Plugin):
    """
    获取字符串类型的Field，直接获取Field的值。

    这个插件只需要执行一次
    """
    name = "FieldValue"
    enabled = True
    tname = None

    def __init__(self, driver, smalidir):
        Plugin.__init__(self, driver, smalidir)

    def run(self):
        print('Run ' + __name__, end=' ', flush=True)
        self.__process()

    def __process(self):
        self.json_list = {
            'type': 'field',
            'data': []
        }
        for sf in self.smalidir:
            json_item = {
                'className': self.smali2java(sf.get_class()),
                'fieldName': []
            }
            for f in sf.get_fields():
                if f.get_type() != 'Ljava/lang/String;':
                    continue

                if f.get_value():
                    continue

                # 格式:如果ID是FieldValue，则直接取对应的Field，不执行解密方法
                json_item['fieldName'].append(f.get_name())
            
            if json_item['fieldName']:
                self.json_list['data'].append(json_item)
        
        self.optimize()

    @staticmethod
    def smali2java(smali_clz):
        return smali_clz.replace('/', '.')[1:-1]

    @staticmethod
    def java2smali(java_clz):
        return 'L' + java_clz.replace('', '/') + ';'

    def optimize(self):
        """
        把Field的值，写回到smali中

        因为Field本来就是唯一，所以，不需要ID，一些繁琐的东西。
        """
        if not self.json_list:
            return
        
        from json import JSONEncoder
        import tempfile
        
        jsons = JSONEncoder().encode(self.json_list)

        outputs = {}
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tfile:
            tfile.write(jsons)
        outputs = self.driver.decode(tfile.name)
        os.unlink(tfile.name)

        if not outputs:
            return False

        if isinstance(outputs, str):
            return False
        
        # print(outputs)

        # 返回结果 类，变量名，值
        # for clz, fvs in outputs.items():
        #     print(clz, fvs)
        for sf in self.smalidir:
            clz = self.smali2java(sf.get_class())
            if clz not in outputs.keys():
                continue
            
            for item in outputs[clz].items():
                self.update_field(sf, item[0], item[1])
        
        self.make_changes = True
        self.smali_files_update()
        self.clear()
        
    def update_field(self, sf, fieldname, value):
        
        for f in sf.get_fields():
            if f.get_name() != fieldname:
                continue
            f.set_value(value)