import sys
from typing import cast, Dict, List

from antlr4 import FileStream, StdinStream, CommonTokenStream, Token, ParserRuleContext

from stella.stellaParser import stellaParser
from stella.stellaLexer import stellaLexer

def ERROR_NONEXHAUSTIVE_MATCH_PATTERNS(pattern: str, ctx: str = ""):
    print("\nERROR_NONEXHAUSTIVE_MATCH_PATTERNS")
    print(f"Text: Pattern '{pattern}' not matched when typechecking '{ctx}'")
    sys.exit(1)
    
def ERROR_ILLEGAL_EMPTY_MATCHING(ctx: str =""):
    print("\nERROR_ILLEGAL_EMPTY_MATCHING")
    print(f"Text: Empty match when typechecking '{ctx}'")
    sys.exit(1)

def ERROR_AMBIGUOUS_SUM_TYPE(ctx: str=""):
    print("\nERROR_AMBIGUOUS_SUM_TYPE")
    print(f"Text: Ambiguous sum type in {ctx}")
    sys.exit(1)

def ERROR_MISSING_MAIN():
    print("\nERROR: ERROR_MISSING_MAIN")
    print("Text: Missing 'main' function")
    sys.exit(1)

def ERROR_UNDEFINED_VARIABLE(var: str):
    print("\nERROR: ERROR_UNDEFINED_VARIABLE")
    print(f"Text: Undefined variable '{var}'")
    sys.exit(1)
    
def ERROR_NOT_A_FUNCTION(var: str, var_type: str, context: str = ""):
    print("\nERROR: ERROR_NOT_A_FUNCTION")
    print(f"Text: Expected a function, but got '{var}' of type '{var_type}' when typechecking '{context}'")
    sys.exit(1)
    
def ERROR_UNEXPECTED_LAMBDA(var: str, var_type: str):
    print("\nERROR: ERROR_UNEXPECTED_LAMBDA")
    print(f"Text: Expected a non-function, but got '{var}' of type '{var_type}'")
    sys.exit(1)
    
def ERROR_UNEXPECTED_TYPE_FOR_PARAMETER(var_type: str, expected_type: str, context: str = ""):
    print("\nERROR: ERROR_UNEXPECTED_TYPE_FOR_PARAMETER")
    print(f"Text: Expected '{expected_type}' but got '{var_type}' when typechecking '{context}'")
    sys.exit(1)

def ERROR_UNEXPECTED_TYPE_FOR_EXPRESSION(var_type: str, expected_type: str, context: str = ""):
    print("\nERROR: ERROR_UNEXPECTED_TYPE_FOR_EXPRESSION")
    print(f"Text: Expected '{expected_type}' but got '{var_type}' when typechecking '{context}'")
    sys.exit(1)
    
def ERROR_TUPLE_INDEX_OUT_OF_BOUNDS(var: str, size: int, index: int, context: str = ""):
    print("\nERROR: ERROR_TUPLE_INDEX_OUT_OF_BOUNDS")
    print(f"Text: Size of tuple '{var}' '{str(size)}' but got index '{index}' when typechecking '{context}'")
    sys.exit(1)
    
def ERROR_UNEXPECTED_TUPLE_LENGTH(size1: int, size2: int):
    print("\nERROR_UNEXPECTED_TUPLE_LENGTH")
    print(f"Text: Expected tuple length '{size1}' but got '{size2}'")
    sys.exit(1)
    
def ERROR_UNEXPECTED_FIELD_ACCESS(var: str, context: str = ""):
    print("\nERROR_UNEXPECTED_FIELD_ACCESS")
    print(f"Text: Unexpected access to '{var}' when typechecking '{context}'")
    sys.exit(1)


def to_readable_type(var) -> str:
    if var == stellaParser.TypeNatContext or isinstance(var, stellaParser.TypeNatContext):
        return "Nat"
    if var == stellaParser.TypeBoolContext or isinstance(var, stellaParser.TypeBoolContext):
        return "Bool"
    if (isinstance(var, stellaParser.DeclFunContext)
        or isinstance(var, stellaParser.TypeFunContext)
        or isinstance(var, stellaParser.AbstractionContext)):
        return "Function"
    if isinstance(var, List):
        if len(var) != 0:
            return "[" + ", ".join(to_readable_type(v) for v in var) + "]"
        return "[]"
    if var == None:
        return "Undefined"
    if var == stellaParser.SuccContext or isinstance(var, stellaParser.SuccContext):
        return "Succ"
    if var == stellaParser.TypeUnitContext:
        return "Unit"
    if (var == stellaParser.TypeTupleContext or isinstance(var, stellaParser.TypeTupleContext)
            or var == stellaParser.TupleContext or isinstance(var, stellaParser.TupleContext)):
        return "Tuple"
    if isinstance(var, stellaParser.RecordContext) or isinstance(var,stellaParser.TypeRecordContext):
        return "Record"
    if isinstance(var, str):
        return var
    if isinstance(var, stellaParser.TypeSumContext):
        return "Sum"
    if isinstance(var, stellaParser.InlContext):
        return "Inl"
    if isinstance(var, stellaParser.InrContext):
        return "Inr"
    print(type(var), "!!")
    return str(var)

class ScopePair():
    var_type: ParserRuleContext
    params: List[ParserRuleContext]
    return_type: ParserRuleContext
    def __init__(self, var_type: ParserRuleContext = None, params: List[ParserRuleContext] = []):
        self.var_type = var_type
        self.params = params
        if is_a_function(var_type):
            if type(var_type) == stellaParser.SuccContext or type(var_type) == stellaParser.PredContext :
                self.return_type = stellaParser.TypeNatContext
                self.params = [stellaParser.TypeNatContext]
            elif type(var_type) == stellaParser.AbstractionContext:
                self.params = var_type.paramDecls
                for i in range(len(self.params)):
                    self.params[i] = handle_expr_context(self.params[i])
                self.return_type = handle_expr_context(var_type.returnExpr)
            elif type(var_type) == stellaParser.TypeFunContext:
                self.params = var_type.paramTypes
                for i in range(len(self.params)):
                    self.params[i] = handle_expr_context(self.params[i])
                self.return_type = handle_expr_context(var_type.returnType)
            elif type(var_type) == stellaParser.DeclFunContext:
                self.params = var_type.paramDecls
                for i in range(len(self.params)):
                    self.params[i] = handle_expr_context(self.params[i])
                self.return_type = handle_expr_context(var_type.returnType)
            else:
                self.return_type = var_type.returnType
        elif (is_a_tuple(var_type)):
            if isinstance(var_type, stellaParser.TypeTupleContext):
                self.params = [None] * len(var_type.types)
                for i in range(len(var_type.types)):
                    self.params[i] = handle_expr_context(var_type.types[i])
                self.return_type = None
            elif isinstance(var_type, stellaParser.TupleContext):
                self.params = [None] * len(var_type.exprs)
                for i in range(len(var_type.exprs)):
                    self.params[i] = handle_expr_context(var_type.exprs[i])
                self.return_type = None
        elif (is_a_record(var_type)):
            if isinstance(var_type, stellaParser.RecordContext):
                self.params = [None] * len(var_type.bindings)
                for i in range(len(var_type.bindings)):
                    self.params[i] = handle_expr_context(var_type.bindings[i])
                self.return_type = None
            else:
                self.params = [None] * len(var_type.fieldTypes)
                for i in range(len(var_type.fieldTypes)):
                    self.params[i] = handle_expr_context(var_type.fieldTypes[i])
                self.return_type = None
        elif (type(var_type) == stellaParser.TypeSumContext):
            self.params = [handle_expr_context(var_type.left), handle_expr_context(var_type.right)]
            self.return_type = None
        else:
            self.return_type = None
        
        
scope_stack: List[Dict[str, ScopePair]] = []

def is_a_function(var: ParserRuleContext):
    if type(var) in [stellaParser.DeclFunContext,
                    stellaParser.TypeFunContext,
                    stellaParser.SuccContext,
                    stellaParser.PredContext,
                    stellaParser.AbstractionContext]:
        return True
    return False

def is_a_tuple(var: ParserRuleContext):
    if type(var) in [stellaParser.TypeTupleContext, stellaParser.TupleContext]:
        return True
    return False

def is_a_record(var: ParserRuleContext):
    if type(var) in [stellaParser.RecordContext, stellaParser.TypeRecordContext]:
        return True
    return False

def enter_scope():
    #print("+ scope")
    scope_stack.append({})

def exit_scope():
    #print("- scope")
    if scope_stack:
        scope_stack.pop()
        
def print_scope():
    for scope in reversed(scope_stack):
        print()
        for name in scope:
            print("name: ", name)
            print("var_type: ", scope[name].var_type)
            print("params: ", scope[name].params)
        
def add_to_scope(name: str, var_type: ParserRuleContext = None):
    if is_a_function(var_type):
        add_func_to_scope(name, var_type)
    elif isinstance(var_type, stellaParser.TypeTupleContext):
        add_tuple_to_scope(name, var_type)
    else:
        add_variable_to_scope(name, handle_expr_context(var_type))

def add_variable_to_scope(name: str, var_type: ParserRuleContext, params: List[ParserRuleContext] = []):
    print(f"Declaring variable '{name}' of type '{to_readable_type(var_type)}'")
    if not scope_stack:
        enter_scope()
    #print(f"Scope id: {len(scope_stack) - 1}")
    scope_stack[-1][name] = ScopePair(var_type)
    
def add_func_to_scope(name: str, var_type: ParserRuleContext, params: List[ParserRuleContext] = []):
    print(f"Declaring func '{name}' of type '{to_readable_type(var_type)}'")
    n = 2
    if type(var_type) != stellaParser.DeclFunContext:
        n = 1
    while len(scope_stack) < n:
        enter_scope()
    #print(f"Scope id: {len(scope_stack) - n}")
    scope_stack[-n][name] = ScopePair(var_type)
    enter_scope()
    
def add_tuple_to_scope(name: str, var_type: ParserRuleContext, params: List[ParserRuleContext] = []):
    print(f"Declaring tuple '{name}' of type '{to_readable_type(type(var_type))}'")
    if not scope_stack:
        enter_scope()
    scope_stack[-1][name] = ScopePair(var_type)
    enter_scope()


def lookup_variable(name: str) -> ScopePair:
    for scope in reversed(scope_stack):
        if name in scope:
            print(f"looked up '{name}' of type '{to_readable_type(scope[name].var_type)}'")
            return scope[name]
    print(f"Couldn't find name '{name}'")
    print(scope_stack)
    return ScopePair()

def handle_expr_context(ctx: stellaParser.ExprContext) -> stellaParser.StellatypeContext:
    match ctx:
        case stellaParser.ConstTrueContext():
            return stellaParser.TypeBoolContext
        
        case stellaParser.ConstFalseContext():
            return stellaParser.TypeBoolContext
        
        case stellaParser.IfContext():
            print(f"Checking if: {ctx.getText()}")
            condition = handle_expr_context(ctx.condition)
            if condition is not stellaParser.TypeBoolContext:
                raise ERROR_UNEXPECTED_TYPE_FOR_EXPRESSION(to_readable_type(condition),
                                                           to_readable_type(stellaParser.TypeBoolContext),
                                                           ctx.getText())
            thenExpr = handle_expr_context(ctx.thenExpr)
            elseExpr = handle_expr_context(ctx.elseExpr)
            if not compare_stuff(thenExpr, elseExpr):
                raise ERROR_UNEXPECTED_TYPE_FOR_EXPRESSION(to_readable_type(elseExpr),
                                                           to_readable_type(thenExpr),
                                                           ctx.getText())
            return [thenExpr, elseExpr]
        
        case stellaParser.VarContext():
            name = ctx.name.text
            var_type = lookup_variable(name).var_type
            if var_type is None:
                ERROR_UNDEFINED_VARIABLE(name)
            return var_type
        
        case stellaParser.TerminatingSemicolonContext():
            return handle_expr_context(ctx.expr())
            
        case stellaParser.ApplicationContext():
            func_type_actual = ctx
            # applying to another application or expression in parenthesis
            if (type(func_type_actual) == stellaParser.ApplicationContext
                or type(func_type_actual) == stellaParser.ParenthesisedExprContext):
                func_type_actual = handle_expr_context(ctx.fun)
            func_to_apply = None
            # applying to function from the scope
            if type(func_type_actual) == stellaParser.VarContext:
                func_to_apply = lookup_variable(func_type_actual.getText())
                func_type_found = func_to_apply.var_type
                if not is_a_function(func_type_found):
                    ERROR_NOT_A_FUNCTION(func_type_actual.getText(), to_readable_type(func_type_found), ctx.getText())
            # context is given, no scope needed
            elif type(func_type_actual) == stellaParser.SuccContext or type(func_type_actual) == stellaParser.PredContext:
                func_to_apply = ScopePair(func_type_actual, [stellaParser.TypeNatContext])
            elif (type(func_type_actual) == stellaParser.AbstractionContext
                or type(func_type_actual) == stellaParser.DeclFunContext):
                func_to_apply = ScopePair(func_type_actual, [handle_expr_context(paramDecl) for paramDecl in func_type_actual.paramDecls])
            elif type(func_type_actual) == stellaParser.TypeFunContext:
                func_to_apply = ScopePair(func_type_actual, func_type_actual.paramTypes)
            else:
                # case not handled yet, TODO: retract unhandled function
                ERROR_NOT_A_FUNCTION(to_readable_type(ctx.fun.getText()), to_readable_type(func_type_actual), ctx.getText())
            if (len(ctx.args) != 0):
                print(f"Applying {ctx.args[0].getText()} to {func_type_actual.getText()}")
            for i in range(len(ctx.args)):
                param1 = handle_expr_context(ctx.args[i])
                param2 = handle_expr_context(func_to_apply.params[i])
                if not compare_stuff(param1, param2):
                    print(type(param1))
                    print(type(param2))
                    ERROR_UNEXPECTED_TYPE_FOR_PARAMETER(to_readable_type(param1), to_readable_type(param2), ctx.getText())
            return func_to_apply.return_type
        
        case stellaParser.SuccContext():
            print(f"Applying {ctx.getText()}")
            n_type = handle_expr_context(ctx.n)
            if n_type is not stellaParser.TypeNatContext:
                ERROR_UNEXPECTED_TYPE_FOR_EXPRESSION(to_readable_type(n_type), to_readable_type(stellaParser.TypeNatContext), ctx.getText())
            return stellaParser.TypeNatContext
        
        case stellaParser.ConstIntContext():
            return stellaParser.TypeNatContext
        
        case stellaParser.AbstractionContext():
            #TODO: sometimes handled twice, for some reason.
            enter_scope()
            try:
                for paramDecl in ctx.paramDecls:
                    add_to_scope(paramDecl.name.text, handle_expr_context(paramDecl))
                handle_expr_context(ctx.returnExpr)
            except: pass
            exit_scope()
            return ctx
        
        case stellaParser.NatRecContext():
            print(f"Applying {ctx.getText()}")
            n_type = handle_expr_context(ctx.n)
            if n_type != stellaParser.TypeNatContext:
                raise TypeError("The first argument of 'Nat::rec' must be of type Nat")
            step_type = handle_expr_context(ctx.step)
            initial_type = handle_expr_context(ctx.initial)
            return initial_type
        
        case stellaParser.ParamDeclContext():
            param_name = ctx.name.text
            param_type = handle_expr_context(ctx.paramType)
            add_to_scope(param_name, param_type)
            return param_type
        
        case stellaParser.ParenthesisedExprContext():
            return handle_expr_context(ctx.expr_)
        
        case stellaParser.TypeParensContext():
            return ctx.type_
        
        case stellaParser.TypeUnitContext():
            return type(ctx)
        
        case stellaParser.ConstUnitContext():
            return stellaParser.TypeUnitContext
        
        case stellaParser.IsZeroContext():
            print(f"Applying {ctx.getText()}")
            n_type = handle_expr_context(ctx.n)
            if n_type is not stellaParser.TypeNatContext:
                ERROR_UNEXPECTED_TYPE_FOR_EXPRESSION(to_readable_type(n_type),
                                                     to_readable_type(stellaParser.TypeNatContext),
                                                     ctx.getText())
            return stellaParser.TypeBoolContext
        
        case stellaParser.TupleContext():
            for param in ctx.exprs:
                handle_expr_context(param)
            return ctx
        
        case stellaParser.TypeTupleContext():
            return ctx
        
        case stellaParser.DotTupleContext():
            found_tuple = ""
            index = int(ctx.getText()[ctx.getText().find('.') + 1:])
            length = 0
            params = []
            if type(ctx.expr_) == stellaParser.ApplicationContext:
                found_tuple = lookup_variable(ctx.expr_.fun.getText())
                length = len(found_tuple.params[0].types)
                sc = ScopePair(found_tuple.params[0])
                params = sc.params
            elif type(ctx.expr_) == stellaParser.VarContext:
                found_tuple = lookup_variable(ctx.expr_.getText())
                length = len(found_tuple.params)
                params = found_tuple.params
            elif type(ctx.expr_) == stellaParser.TupleContext:
                found_tuple = ScopePair(ctx.expr_)
                length = len(found_tuple.params)
                params = found_tuple.params
            if index > length:
                ERROR_TUPLE_INDEX_OUT_OF_BOUNDS(ctx.expr_.getText(), len(params), index, ctx.getText())
            return handle_expr_context(params[index - 1])
        
        case stellaParser.TypeRecordContext():
            for fieldtype in ctx.fieldTypes:
                handle_expr_context(fieldtype)
            return ctx
        
        case stellaParser.RecordFieldTypeContext():
            type_to_return = handle_expr_context(ctx.type_)
            add_to_scope(ctx.label.text, type_to_return)
            return type_to_return
        
        case stellaParser.RecordContext():
            for binding in ctx.bindings:
                handle_expr_context(binding)
            return ctx
        
        case stellaParser.BindingContext():
            return handle_expr_context(ctx.rhs)
        
        case stellaParser.DotRecordContext():
            handled_left_part = handle_expr_context(ctx.expr_)
            for i in range(len(handled_left_part.fieldTypes)):
                if (ctx.label.text == handled_left_part.fieldTypes[i].label.text):
                    return handle_expr_context(handled_left_part.fieldTypes[i].type_)
            ERROR_UNEXPECTED_FIELD_ACCESS(ctx.label.text, ctx.getText())
            
        case stellaParser.LetContext():
            enter_scope()
            for patternBinding in ctx.patternBindings:
                add_to_scope(patternBinding.pat.name.text, handle_expr_context(patternBinding.rhs))
            returnType = handle_expr_context(ctx.body)
            exit_scope()
            return returnType
        
        case stellaParser.TypeSumContext():
            if not handle_expr_context(ctx.left) or not handle_expr_context(ctx.right):
                ERROR_AMBIGUOUS_SUM_TYPE(ctx.getText())
            return ctx
        
        case stellaParser.InlContext():
            handle_expr_context(ctx.expr_)
            return ctx
        
        case stellaParser.InrContext():
            handle_expr_context(ctx.expr_)
            return ctx
        
        case stellaParser.MatchContext():
            got = handle_expr_context(ctx.expr_)
            if not isinstance(got, stellaParser.TypeSumContext):
                ERROR_AMBIGUOUS_SUM_TYPE(got.getText())
            if len(ctx.cases) == 0:
                ERROR_ILLEGAL_EMPTY_MATCHING(ctx.getText())
            f_left = False
            f_right = False
            to_return = [None] * len(ctx.cases)
            for i in range(len(ctx.cases)):
                needed_type = ''
                if type(ctx.cases[i].pattern_) == stellaParser.PatternInlContext:
                    needed_type = handle_expr_context(got.left)
                    f_left = True
                else:
                    needed_type = handle_expr_context(got.right) 
                    f_right = True
                add_to_scope(ctx.cases[i].pattern_.pattern_.name.text, needed_type)
                to_return[i] = handle_expr_context(ctx.cases[i].expr_)
            if not f_left or not f_right:
                ERROR_NONEXHAUSTIVE_MATCH_PATTERNS("Inl()" if f_right else "Inr()", ctx.getText())
            return to_return
        
        case _:
            if (ctx == stellaParser.TypeNatContext or 
                ctx == stellaParser.TypeBoolContext or
                ctx == stellaParser.TypeUnitContext or
                type(ctx) == stellaParser.TypeFunContext or
                ctx == stellaParser.PatternVarContext):
                return ctx
            if (type(ctx) == stellaParser.TypeNatContext or 
                type(ctx) == stellaParser.TypeUnitContext or
                type(ctx) == stellaParser.TypeBoolContext):
                return type(ctx)
            print(ctx)
            print(type(ctx))
            print(ctx.getText())
            raise RuntimeError("unsupported syntax")


def handle_decl_context(ctx: stellaParser.DeclContext):
    match ctx:
        case stellaParser.DeclFunContext():
            name = cast(Token, ctx.name)
            print("_________________\n")
            print("DECLARING FUNCTION", name.text)
            print("_________________")
            enter_scope()
            add_to_scope(name.text, ctx)
            for localDecl in ctx.localDecls:
                handle_decl_context(localDecl)
            handled_return_expr = handle_expr_context(ctx.returnExpr)
            return_type = handle_expr_context(ctx.returnType)
            if not compare_stuff(handled_return_expr, return_type):
                ERROR_UNEXPECTED_TYPE_FOR_EXPRESSION(to_readable_type(handled_return_expr), to_readable_type(return_type), ctx.getText())
            exit_scope()
            print()
        case stellaParser.DeclTypeAliasContext():
            raise RuntimeError("unsupported syntax")
        case _:
            raise RuntimeError("unsupported syntax")
        

def compare_stuff(stuff1, stuff2) -> bool:
    if is_a_function(stuff1) and is_a_function(stuff2):
        stuff1 = ScopePair(stuff1)
        stuff2 = ScopePair(stuff2)
        for i in range(len(stuff1.params)):
            if not compare_stuff(stuff1.params[i], stuff2.params[i]):
                return False
        return compare_stuff(stuff1.return_type, stuff2.return_type)
    if is_a_tuple(stuff1) and is_a_tuple(stuff2):
        stuff1 = ScopePair(stuff1)
        stuff2 = ScopePair(stuff2)
        if len(stuff1.params) != len(stuff2.params):
            ERROR_UNEXPECTED_TUPLE_LENGTH(len(stuff2.params), len(stuff1.params))
        for i in range(len(stuff1.params)):
            if not compare_stuff(stuff1.params[i], stuff2.params[i]):
                return False
        return True
    if is_a_record(stuff1) and is_a_record(stuff2):
        stuff1 = ScopePair(stuff1)
        stuff2 = ScopePair(stuff2)
        for i in range(len(stuff1.params)):
            if not compare_stuff(stuff1.params[i], stuff2.params[i]):
                return False
        return True
    if (type(stuff1) in [stellaParser.InlContext, stellaParser.InrContext] and
        type(stuff2) in [stellaParser.InlContext, stellaParser.InrContext]):
        return True
    if (type(stuff2) == stellaParser.TypeSumContext):
        stuff2 = ScopePair(stuff2)
        if not isinstance(stuff1, List):
            #i = 0 if type(stuff1) == stellaParser.InlContext else 1
            #got = handle_expr_context(stuff1.expr_)
            #return compare_stuff(got, stuff2.params[i])
            ERROR_AMBIGUOUS_SUM_TYPE(stuff1.getText())
        for stuff in stuff1:            
            i = 0 if type(stuff) == stellaParser.InlContext else 1
            if not compare_stuff(stuff2.params[i], handle_expr_context(stuff.expr_)):
                return False
        return True
    if isinstance(stuff1, List):
        for stuff in stuff1:
            if not compare_stuff(stuff, stuff2):
                return False
        return True
    return (stuff1 == stuff2)


def handle_program_context(ctx: stellaParser.ProgramContext):
    main_found = any(
        isinstance(decl, stellaParser.DeclFunContext) and decl.name.text == "main"
        for decl in ctx.decls
    )
    if not main_found:
        ERROR_MISSING_MAIN()
    enter_scope()
    for decl in ctx.decls:
        handle_decl_context(decl)
    print("Congrats, input program is well-typed, no retake today, fella")


def main(argv):
    if len(argv) > 1:
        input_stream = FileStream(argv[1])
    else:
        #input_stream = StdinStream()
        input_stream = FileStream("tests/ill-typed/-DONE-non-exhaustive.stella")
    lexer = stellaLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = stellaParser(stream)

    program = parser.program()
    handle_program_context(program)


if __name__ == '__main__':
    main(sys.argv)
