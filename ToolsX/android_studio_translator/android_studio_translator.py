from xml.etree import ElementTree as Et

from xx import encodex
from xx import filex
from xx import iox

import re


class AndroidStudioTranslator:
    def main(self):
        # 1原文件
        en_file = 'data/ActionsBundle_en.properties'
        # 2汉化文件
        unicode_file = 'data/ActionsBundle_unicode.properties'
        # 3转为中文
        cn_file = 'data/ActionsBundle_cn.properties'
        # 4修改断句的文件
        cn_modified_file = 'data/ActionsBundle_cn_modified.properties'
        # 5处理快捷方式的文件
        cn_modified_shortcut_file = 'data/ActionsBundle_cn_modified_shortcut.properties'
        # 6手动完成的keymap文件
        keymap_file = 'data/keymap.txt'
        action_list = [
            ['退出', exit],
            ['参照翻译(未翻译保留)', self.translate_file_by_reference, en_file, cn_modified_file],
            ['参照翻译(未翻译标记)', self.translate_file_by_reference, en_file, cn_modified_file, None, '%s=%s【未翻译】'],
            ['将文件的unicode转为中文', self.change_unicode_to_chinese, unicode_file, cn_file],
            ['将文件的中文转为unicode', self.change_chinese_to_unicode, cn_file],
            ['处理快捷方式（未翻译留空）', self.handle_shortcut, en_file, cn_modified_file, cn_modified_shortcut_file],
            ['将中文翻译结果导出为OmegaT数据', self.convert_to_omegat_dict, en_file, cn_modified_shortcut_file,
             'data/project_save.tmx.xml'],
            ['处理keymap文件', self.handle_keymap_file, en_file, keymap_file],
        ]
        iox.choose_action(action_list)

    @staticmethod
    def change_unicode_to_chinese(file_path, output_file=None):
        """
        将unicode转为中文
        :param file_path:源文件 
        :param output_file: 输出文件
        :return: 
        """
        if output_file is None:
            output_file = filex.get_result_file_name(file_path, '_cn_result')

        lines = filex.read_lines(file_path)
        if lines is None:
            return

        result = []
        for line in lines:
            line = line.replace('\n', '')
            if '=' in line:
                key_value = line.split('=', 1)
                line = '%s=%s' % (key_value[0], encodex.unicode_str_to_chinese(key_value[1]))
            result.append(line + '\n')
        filex.write_lines(output_file, result)

    @staticmethod
    def change_chinese_to_unicode(file_path, output_file=None):
        """
        将中文转为unicode
        :param file_path: 
        :param output_file: 
        :return: 
        """
        if output_file is None:
            output_file = filex.get_result_file_name(file_path, '_unicode_result')

        lines = filex.read_lines(file_path)
        if lines is None:
            return

        result = []
        for line in lines:
            line = line.replace('\n', '')
            if '=' in line:
                key_value = line.split('=', 1)
                line = '%s=%s' % (key_value[0], encodex.chinese_to_unicode(key_value[1]))
            result.append(line + '\n')
        filex.write_lines(output_file, result)

    def handle_shortcut(self, en_file, cn_file, result_file=None):
        """
        处理快捷键，将_字母替换为(_字母)
        :param en_file: 
        :param cn_file: 
        :param result_file: 
        :return: 
        """
        if result_file is None:
            result_file = filex.get_result_file_name(cn_file, '_shortcut_result')

        en_dict = filex.get_dict_from_file(en_file)
        cn_dict = filex.get_dict_from_file(cn_file)
        count = 0
        for (k, v) in en_dict.items():
            if '_' in v:
                index = v.find('_')
                shortcut = v[index + 1:index + 2]
                # 包含快捷键
                if k in cn_dict.keys():
                    # 都有
                    cn_value = cn_dict[k]
                    count += 1
                    # 已经是(_字母结)结尾的，重新替换一遍
                    p = re.compile(r'(.*)(\(_\w\))')
                    if re.match(p, cn_value) is not None:
                        replace_result = re.sub(p, r'\1' + '(_%s)' % shortcut, cn_value)
                        print('替换%d,key=%s,v=%s,cn=%s,r=%s' % (count, shortcut, v, cn_value, replace_result))
                    else:
                        replace_result = cn_value.replace('_', '') + '(_%s)' % shortcut
                        print('添加%d,key=%s,v=%s,cn=%s,r=%s' % (count, shortcut, v, cn_value, replace_result))
                    cn_dict[k] = replace_result
        result = self.translate_file_by_dict(en_file, cn_dict, '')  # 重新翻译
        filex.write_lines(result_file, result)

    def translate_file_by_reference(self, en_file, cn_file, result_file=None, untranslated_replace=None):
        """
        根据参考翻译文件
        :param en_file:英文 
        :param cn_file: 参考中文
        :param result_file: 结果文件
        :param untranslated_replace:未翻译时替换 
        :return: 
        """
        if result_file is None:
            result_file = filex.get_result_file_name(en_file, '_translation_result')

        translation_dict = filex.get_dict_from_file(cn_file)
        result = self.translate_file_by_dict(en_file, translation_dict, untranslated_replace)

        filex.write_lines(result_file, result)

    @staticmethod
    def translate_file_by_dict(file_path, translation_dict, untranslated_replace=None):
        """
        翻译文件
        :param file_path: 要翻译的文件
        :param translation_dict: 字典
        :param untranslated_replace: 未翻译的用什么替换，（将会执行untranslated % (key_value[0], key_value[1])），
        如果执行失败则直接用其值替换
        默认为None，如果为None表示不替换
        :return: 
        """
        lines = filex.read_lines(file_path)
        if lines is None:
            return None

        result = []
        untranslated_count = 0
        for line in lines:
            line = line.replace('\n', '')
            if '=' in line:
                key_value = line.split('=', 1)
                # 翻译
                key = key_value[0]
                if key in translation_dict.keys():
                    translation = translation_dict[key]
                    if translation is not None and translation != '':
                        line = '%s=%s' % (key_value[0], translation)
                else:
                    # line += '待翻译'
                    untranslated_count += 1
                    print('%d-%s-未翻译' % (untranslated_count, line))
                    if untranslated_replace is not None:
                        try:
                            line = untranslated_replace % (key_value[0], key_value[1])
                        except TypeError:
                            line = untranslated_replace
            result.append(line + '\n')
        return result

    def convert_to_omegat_dict(self, en_file, cn_file, output_file=None):
        """
        将翻译结果转为omegaT的字典
        :param en_file: 英文文件
        :param cn_file: 中文文件
        :param output_file: 输出文件
        :return: 
        """
        if output_file is None:
            output_file = filex.get_result_file_name(cn_file, '_omegat_result', 'xml')

        en_dict = filex.get_dict_from_file(en_file)
        cn_dict = filex.get_dict_from_file(cn_file)

        tmx = Et.Element('tmx')
        tmx.attrib['version'] = '1.1'
        Et.SubElement(tmx, 'header')
        body = Et.SubElement(tmx, 'body')
        for (k, v) in cn_dict.items():
            if k in en_dict.keys():
                en_value = en_dict[k]
                cn_value = v
                # 判断是否有多个句子，"."加一个空格
                added = False
                if '. ' in en_value:
                    en_split = en_value.split('. ')
                    if en_split[1] != '':
                        # 包含“.”，不是在最后的“...”
                        # 检查中文
                        if '。 ' in cn_value:
                            cn_split = cn_value.split('。 ')
                            if len(en_split) == len(cn_split):
                                added = True
                                # 中英长度相等
                                for i in range(len(en_split)):
                                    self.add_translate_element(body, en_split[i], cn_split[i])
                                    print('分开添加:' + cn_split[i])
                            else:
                                print('')
                                print(en_value)
                                print(cn_value)
                                print('%d,%d' % (len(en_split), len(cn_split)))
                        else:
                            print('')
                            print(en_value)
                            print(cn_value)
                            print('不包含')
                if not added:
                    self.add_translate_element(body, en_value, cn_value)

        tree = Et.ElementTree(tmx)
        tree.write(output_file, encoding='utf-8')
        print('输出为' + output_file)

    @staticmethod
    def add_translate_element(element, en, cn):
        """
        向element中添加一个翻译
        :param element: 
        :param en
        :param cn
        :return: 
        """

        tu = Et.SubElement(element, 'tu')
        # 英文
        tuv = Et.SubElement(tu, 'tuv')
        tuv.attrib['lang'] = 'EN-US'
        seg = Et.SubElement(tuv, 'seg')
        seg.text = en
        # 中文
        tuv2 = Et.SubElement(tu, 'tuv')
        tuv2.attrib['lang'] = 'ZH-CN'
        seg2 = Et.SubElement(tuv2, 'seg')
        seg2.text = cn

    @staticmethod
    def handle_keymap_file(en_file, cn_file, result_file=None):
        """
        将一行一行的keymap重新处理
        导出为.properties，这样OmegaT处理时会换照配置文件去处理
        我们以[#]或[desc]加空格为开头，会被过滤器正确解析
        :param en_file: 
        :param cn_file: 
        :param result_file: 
        :return: 
        """
        if result_file is None:
            result_file = filex.get_result_file_name(cn_file, '_with_desc', 'properties')

        lines = filex.read_lines(cn_file)
        if lines is None:
            return

        en_dict = filex.get_dict_from_file(en_file)
        # 反转
        reversed_dict = {value: key for key, value in en_dict.items()}

        count = 0
        desc_count = 0
        result = []
        for line in lines:
            line = line.replace('\n', '')
            if line.startswith('#'):
                old_line = line
                # 因为有加了#，所以处理下
                line = line.lstrip('# ')
                # 相差的长度是trip掉的，注意在替换了\n之后
                prefix = old_line[0:len(old_line) - len(line)]
            else:
                prefix = '#' * 5
            append = ''
            if line in reversed_dict.keys():
                count += 1
                key = reversed_dict[line]
                if key.endswith('.text'):
                    desc_key = key[:-len('.text')] + '.description'
                    if desc_key in en_dict.keys():
                        desc = en_dict[desc_key]
                        desc_count += 1
                        print('%d/%d,%s,key=%s,desc=%s' % (count, desc_count, line, key, desc))
                        # 有描述，添加
                        append = '\n\n%s %s' % ('[desc]', desc)
            line = '\n\n[%s] %s%s' % (prefix, line, append)
            result.append(line)
        filex.write_lines(result_file, result)


if __name__ == '__main__':
    AndroidStudioTranslator().main()