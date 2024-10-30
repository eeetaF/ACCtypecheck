import sys
from typing import cast, Dict, List, Optional

from antlr4 import FileStream, StdinStream, CommonTokenStream, Token, ParserRuleContext

from stella.stellaParser import stellaParser
from stella.stellaLexer import stellaLexer

class ScopePair():
    var_type: ParserRuleContext
    params: List[ParserRuleContext]
    def __init__(self, var_type: ParserRuleContext = None, params: List[ParserRuleContext] = None):
        self.var_type = var_type
        self.params = params
        
scope_stack: List[Dict[str, ScopePair]] = []

def enter_scope():
    scope_stack.append({})

def exit_scope():
    if scope_stack:
        scope_stack.pop()
        
def print_scope():
    for scope in reversed(scope_stack):
        print()
        for name in scope:
            print("name: ", name)
            print("var_type: ", scope[name].var_type)
            print("params: ", scope[name].params)
        
def add_to_scope(name: str, var_type: ParserRuleContext):
    if isinstance(var_type, stellaParser.TypeFunContext):
        params = var_type.paramTypes
        for i in range(len(params)):
            params[i] = handle_expr_context(params[i])
        add_func_to_scope(name, var_type, params)
    elif isinstance(var_type, stellaParser.DeclFunContext) or isinstance(var_type, stellaParser.AbstractionContext):
        params = var_type.paramDecls
        for i in range(len(params)):
            params[i] = handle_expr_context(params[i])
        add_func_to_scope(name, var_type, params)
    else:
        add_variable_to_scope(name, type(var_type))

def add_variable_to_scope(name: str, var_type: ParserRuleContext, params: List[ParserRuleContext] = []):
    print("Adding var to scope:", name, var_type, params)
    if not scope_stack:
        enter_scope()
    scope_stack[-1][name] = ScopePair(var_type, params)
    
def add_func_to_scope(name: str, var_type: ParserRuleContext, params: List[ParserRuleContext] = []):
    print("Adding func to scope:", name, var_type, params)
    while len(scope_stack) < 2:
        enter_scope()
    scope_stack[-2][name] = ScopePair(var_type, params)

def lookup_variable(name: str) -> ScopePair:
    for scope in reversed(scope_stack):
        if name in scope:
            return scope[name]
    return ScopePair()

def handle_expr_context(ctx: stellaParser.ExprContext) -> stellaParser.StellatypeContext:
    match ctx:
        case stellaParser.ConstTrueContext():
            return stellaParser.TypeBoolContext
        
        case stellaParser.ConstFalseContext():
            return stellaParser.TypeBoolContext
        
        case stellaParser.IfContext():
            print(type(ctx.condition))
            condition = handle_expr_context(cast(stellaParser.ExprContext, ctx.condition))
            if condition is not stellaParser.TypeBoolContext:
                raise TypeError(f"Condition must be Bool")
            thenExpr = handle_expr_context(cast(stellaParser.ExprContext, ctx.thenExpr))
            elseExpr = handle_expr_context(cast(stellaParser.ExprContext, ctx.elseExpr))
            if thenExpr is not elseExpr:
                raise TypeError("Mismatched types in 'then' and 'else' branches of if-expression.")
            return thenExpr
        
        case stellaParser.VarContext():
            name = cast(Token, ctx.name).text
            var_type = lookup_variable(name).var_type
            if var_type is None:
                raise TypeError(f"Undefined variable '{name}'")
            return var_type
        
        case stellaParser.TerminatingSemicolonContext():
            return handle_expr_context(ctx.expr())
            
        case stellaParser.ApplicationContext():
            #TODO handle application to abstract function
            func_type_actual = ctx.fun
            if type(func_type_actual) == stellaParser.ApplicationContext or type(func_type_actual) == stellaParser.ParenthesisedExprContext:
                func_type_actual = handle_expr_context(func_type_actual)
            if type(func_type_actual) != stellaParser.TypeFunContext:
                func_name = func_type_actual.getText()
                looked_up_var = lookup_variable(func_name)
                func_type_found = looked_up_var.var_type
                print(f"Applying {ctx.args[0].getText()} to {func_name}")
                if (not type(func_type_found) == stellaParser.DeclFunContext and
                    not type(func_type_found) == stellaParser.TypeFunContext):
                    raise TypeError(f"Attempted to call a non-function '{func_name}'")
                if len(ctx.args) != len(looked_up_var.params):
                    raise TypeError(f"Mismatch number of params, got '{len(ctx.args)}' expected '{len(looked_up_var.params)}' in '{func_name}'")
                for i in range(len(ctx.args)):
                    param1 = handle_expr_context(ctx.args[i])
                    param2 = ""
                    if (looked_up_var.params[i] in [stellaParser.TypeNatContext, stellaParser.TypeBoolContext]):
                        param2 = looked_up_var.params[i]
                    else:
                        print((looked_up_var.params[i].getText()))
                        param2 = handle_expr_context(looked_up_var.params[i])
                    if param1 != param2:
                        raise TypeError(f"Mismatch params.\n[{i}]Param of call '{func_name}':\nExpected\n'{param2.get("parametersTypes")[i]}'\ngot\n'{param1.get("parametersTypes")[i]}'")
                return type(func_type_found.returnType)
            return func_type_actual.returnType
        
        case stellaParser.SuccContext():
            n_type = handle_expr_context(ctx.n)
            if n_type is not stellaParser.TypeNatContext:
                raise TypeError(f"Argument of 'succ' must be 'Nat'")
            return stellaParser.TypeNatContext
        
        case stellaParser.ConstIntContext():
            return stellaParser.TypeNatContext
        
        case stellaParser.AbstractionContext():
            enter_scope()
            param_types = []
            for paramDecl in ctx.paramDecls:
                param_type = paramDecl.paramType
                add_to_scope(paramDecl.name.text, param_type)
                param_types.append(type(param_type))
            return_type = handle_expr_context(ctx.returnExpr)
            exit_scope()
            return {
                "parametersTypes": param_types,
                "returnType": return_type,
            }
        
        case stellaParser.NatRecContext():
            n_type = handle_expr_context(ctx.n)
            if n_type != stellaParser.TypeNatContext:
                raise TypeError("The first argument of 'Nat::rec' must be of type Nat")
            step_type = handle_expr_context(ctx.step)
            initial_type = handle_expr_context(ctx.initial)
            return initial_type
        
        case stellaParser.ParamDeclContext():
            param_name = ctx.name.text
            param_type = ctx.paramType
            add_to_scope(param_name, param_type)
            return param_type
        
        case stellaParser.ParenthesisedExprContext():
            return handle_expr_context(ctx.expr_)
        
        case _:
            if (ctx == stellaParser.TypeNatContext or 
                ctx == stellaParser.TypeBoolContext):
                return ctx
            if (type(ctx) == stellaParser.TypeNatContext or 
                type(ctx) == stellaParser.TypeBoolContext):
                return type(ctx)
            if (type(ctx) == stellaParser.TypeFunContext):
                param_types = []
                for paramType in ctx.paramTypes:
                    param_types.append(paramType)
                return_type = handle_expr_context(ctx.returnType)
                return {
                    "parametersTypes": param_types,
                    "returnType": return_type,
                }
            raise RuntimeError("unsupported syntax")


def handle_decl_context(ctx: stellaParser.DeclContext):
    match ctx:
        case stellaParser.DeclFunContext():
            name = cast(Token, ctx.name)
            print("_________________")
            print("FUNCTION", name.text)
            print("_________________")
            returnType = cast(stellaParser.ExprContext, ctx.returnExpr)
            enter_scope()
            add_to_scope(name.text, ctx)
            handle_expr_context(returnType)
            exit_scope()
            print()
        case stellaParser.DeclTypeAliasContext():
            raise RuntimeError("unsupported syntax")
        case _:
            raise RuntimeError("unsupported syntax")


def handle_program_context(ctx: stellaParser.ProgramContext):
    main_found = any(
        isinstance(decl, stellaParser.DeclFunContext) and decl.name.text == "main"
        for decl in ctx.decls
    )
    if not main_found:
        raise RuntimeError("No 'main' function")
    for decl in ctx.decls:
        handle_decl_context(decl)
    print("All good fella")


def main(argv):
    if sys.version_info.major < 3 or sys.version_info.minor < 10:
        raise RuntimeError('Python 3.10 or a more recent version is required.')
    if len(argv) > 1:
        input_stream = FileStream(argv[1])
    else:
        #input_stream = StdinStream()
        input_stream = FileStream("tests/ill-typed/shadowed-variable-1.stella")
    lexer = stellaLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = stellaParser(stream)

    program = parser.program()
    handle_program_context(program)


if __name__ == '__main__':
    main(sys.argv)
