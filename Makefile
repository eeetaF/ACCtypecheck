JAVA=java
JAVA_FLAGS=-Xmx500M -cp "${HOME}/.java/jar/antlr-4.12.0-complete.jar:${CLASSPATH}"
PARSER=${JAVA} ${JAVA_FLAGS} org.antlr.v4.Tool
PARSER_FLAGS=-lib stella -package stella -Dlanguage=Python3
LEXER=${JAVA} ${JAVA_FLAGS} org.antlr.v4.Tool
LEXER_FLAGS=-lib stella -package stella -Dlanguage=Python3

all: src/stella/stellaParser.py

typecheck: src/interpret.py src/stella/stellaLexer.py src/stella/stellaParser.py
	python3 src/interpret.py

interpret: src/interpret.py src/stella/stellaLexer.py src/stella/stellaParser.py
	python3 src/interpret.py $(STELLA_FILE)

src/stella/stellaLexer.py: src/stella/stellaLexer.g4
	cd src/ && (${LEXER} ${LEXER_FLAGS} stella/stellaLexer.g4; cd ../)

src/stella/stellaParser.py: src/stella/stellaLexer.py src/stella/stellaParser.g4
	cd src/ && (${PARSER} ${PARSER_FLAGS} stella/stellaParser.g4; cd ../)

.PHONY: all typecheck interpret
