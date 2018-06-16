import dis


class PreProcessorError(Exception):
    pass


class PreProcessor(object):
    """
        Parse code string to change the functionality before compiled to bytecode
        

    """
    pre_prefix_1 = '#-ifdef'    # if
    pre_prefix_2 = '#-ifndef'   # if not
    pre_suffix = '#-endif'      # end commenting

    
    @classmethod
    def parseCode(cls, codeString, **kw):
        """
            
        """
        apply_comment = False
        code = codeString.split('\n')

        for enum, parse in enumerate(code[:]):
            line = parse.replace(' ', '')

            if line.startswith((cls.pre_prefix_1, cls.pre_prefix_2)):
                stmt = line.split('/')

                if not kw[stmt[1]]: apply_comment = True
                
                continue

            # End line commenting
            elif line.startswith(cls.pre_suffix): apply_comment = False

            # Apply comments
            if apply_comment: code[enum] = '#{}'.format(line)         
    
        return '\n'.join(code)

    @classmethod
    def printStringCode(cls, string):
        """
            Print the string code

            return -> None

        """
        for s in string:
            print s
    
    @classmethod
    def printByteCode(cls, func):
        """
            Disassemble func to bytecode

            return -> None
        """
        if not callable(func): raise TypeError 
        dis.dis(func)


if __name__ == '__main__':
    pass
