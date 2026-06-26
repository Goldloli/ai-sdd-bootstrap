package {{PACKAGE}}

// Harness: {{TITLE}}
//
// Purpose:
// {{PURPOSE}}
//
// Related spec: {{RELATED_SPEC}}
//
// TODO: Replace this draft harness with real inputs and expected outputs.
//       It intentionally fails until you wire up real assertions.
//
// If the package under test is not in this directory, change the package
// name to {{PACKAGE}}_test and import your module path.

import "testing"

func Test{{PASCAL_SLUG}}(t *testing.T) {
	t.Fatalf("Replace this draft harness with real assertions before counting it as coverage.")
}
