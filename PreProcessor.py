

class PreProcessorError(Exception):
    pass


class PreProcessor(object):
    """
        Parse code string to change the functionality before compiled to bytecode
        control which part of the code is turned in to bytecode using the ifdef/ifndef - endif

    """
    pre_prefix_1 = '#-ifdef'    # if defined
    pre_prefix_2 = '#-ifndef'   # if not defined
    pre_suffix =   '#-endif'    # end commenting

    
    @classmethod
    def parseCode(cls, codeString, **kw):
        """
            Parse code strings using very primitive C-style preprocessor directives
            abuses Python removing commented lines

            exec(PreProcessor.parseCode(
            def foo():
                
                #-ifdef/value
                print "This block will not be turned into bytecode"
                print "This block will not be turned into bytecode"
                print "This block will not be turned into bytecode"
                print "This block will not be turned into bytecode"
                #-endif
                
                print "This will be turned into bytecode"
            
            , value=0))

            codeString -> Code string
            kw -> Variables controlling the defines (Need to match the directive values!)

        """
        apply_comment = False
        code = codeString.split('\n')

        for enum, parse in enumerate(code[:]):
            line = parse.replace(' ', '')

            if line.startswith((cls.pre_prefix_1, cls.pre_prefix_2)):
                try:
                    directive, value = line.split('/')
                except:
                    raise PreProcessorError("Make sure the directive is correct and value matches the directive value!") 
                
                if directive == cls.pre_prefix_1:
                    if not kw[value]: apply_comment = True

                elif directive == cls.pre_prefix_2:
                    if kw[value]: apply_comment = True
                
                continue

            # End line commenting
            elif line.startswith(cls.pre_suffix): 
                apply_comment = False

            # Apply comments
            if apply_comment: 
                code[enum] = '#{}'.format(line)         

        return '\n'.join(code)

    
    @classmethod
    def printStringCode(cls, string):
        """
            Print the string code

            return -> None

        """
        for line in string:
            print line
    
    
    @staticmethod
    def printByteCode(cls, func):
        """
            Disassemble func to bytecode

            return -> None
        """
        import dis
        if not callable(func): raise TypeError 
        dis.dis(func)


if __name__ == '__main__':
    exec(PreProcessor.parseCode("""
def test():

    #-ifndef/dothis
    print "First line!"
    #-endif
    
    #-ifdef/dothis
    print "Second line!"
    #-endif

    """, dothis=0))
