# versão recursiva e versão iterativa do fibonacci

fn fib(n) {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}

fn fibIter(n) {
    let a = 0;
    let b = 1;
    let i = 0;
    while (i < n) {
        let tmp = a + b;
        a = b;
        b = tmp;
        i = i + 1;
    }
    return a;
}

let i = 0;
while (i <= 10) {
    print("fib(" + str(i) + ") =", fib(i));
    i = i + 1;
}

print("fib(80) iterativo =", fibIter(80));
