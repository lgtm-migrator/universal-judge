package dodona

import groovy.json.JsonBuilder
import groovy.transform.CompileStatic

@CompileStatic
class Evaluator {
    String name
    String type
    String language
    List<String> options

    Evaluator(String name = "textComparator", String type = "builtin", String language = null, List<String> options = []) {
        this.name = name
        this.type = type
        this.language = language
        this.options = options
    }

    void name(String name) {
        this.name = name
    }

    void type(String type) {
        this.type = type
    }

    void language(String language) {
        this.language = language
    }

    void options(List<String> options) {
        this.options = options
    }
}

@CompileStatic
class Evaluators implements WithClosureResolver {
    Evaluator stdout = new Evaluator()
    Evaluator stderr = new Evaluator()
    Evaluator file = new Evaluator(name: "fileComparator")

    def stdout(@DelegatesTo(value = Evaluator, strategy = Closure.DELEGATE_FIRST) Closure<?> cl) {
        def evaluator = resolve(Evaluator, cl)
        this.stdout = evaluator
    }

    def stderr(@DelegatesTo(value = Evaluator, strategy = Closure.DELEGATE_FIRST) Closure<?> cl) {
        def evaluator = resolve(Evaluator, cl)
        this.stderr = evaluator
    }

    def file(@DelegatesTo(value = Evaluator, strategy = Closure.DELEGATE_FIRST) Closure<?> cl) {
        def evaluator = resolve(Evaluator, cl)
        this.file = evaluator
    }

    Object toJson() {
        def builder = new JsonBuilder()
        builder stdout: this.stdout,
                stderr: this.stderr,
                file: this.file
        return builder.content
    }
}
