# Module API Review Notes

## Current Major Limitations
- Only local state is supported
- Only the `aws-base` module works so far. Module type aliases do not work, so it must still be referenced as `aws-base`.
- Only the `apply` command works. To clean up, run `terraform destroy`
- Multiple opta files (i.e. environments or peer opta files) are not supported

## New Concepts & Major Changes
### References
The `opta.utils.ref` module contains the `Reference` class, which is a type that is used to store loose references to nested values within an object.
A `Reference` internally is just a tuple of strings and ints, with each item in the tuple referring to the next nested subkey.
For example, the reference `foo.1.bar` when viewed against object `ham` is roughly equivalent to `ham["foo"][1]["bar"]`.
Note that `Reference` objects do not have pointers to any parent object themselves.
They are mostly used to refer to module inputs and outputs.

The `SimpleInterpolatedReference` and `ComplexInterpolatedReference` types add support for writing `Reference`s in opta files using the `${foo.bar}` syntax (very similar to terraform's interpolation syntax).
`SimpleInterpolatedReference` refers to a string that only contains a single reference and no other content.
`ComplexInterpolatedReference` refers to a string that has a mix of literal string content and multiple `SimpleInterpolatedReference`s.

### Visitor
The `opta.utils.visit.Visitor` class is a utility to make `Reference`s easy to work with, as well as recursively iterating over a collection object.
A `Visitor` object can be indexed using a reference to recursively access a value within a root object.
For example, `v = Visitor(foo); v[Reference.parse("spam.ham")]` is nearly equivalent to `foo["spam"]["ham"]`.
It becomes more powerful when setting nested values, as using the `set` method instead of an index allows the caller to automatically fill in any missing intermediate values.

The other use for `Visitor` is recursively iterating over an arbitrarily large collection (but it does not support recursive collections).
If you iterate on a `Visitor`, it will return a (`ref`, `value`) tuple on each iteration with `ref` being a `Reference` to the current value and `value` is that value.
If you want to modify the value at that reference, you can use `visitor[ref] = new_value`.
The `depth_first`, `filter`, and `builder` arguments to the `Visitor` constructor can be used to control the iteration behavior.

### Linker
The `Linker` object (in `opta.linker`) is responsible for forming the connections (links) between different modules in a module file.
It contains various linking passes to parse interpolations, discover implicit, automatic, and manual links, set inputs, and determine module execution order.
As-is, its a little messy, but hopefully not too confusing to understand.
Overall, its probably the most complex piece of the module API.

### Business Logic Separated from Data
As part of the Module API, business logic (as it relates to generating and running Terraform) has been separated out from the data structures (namely `Layer` and `Module`).
This should hopefully give the different classes have a clearer focus and make future additions easier.
