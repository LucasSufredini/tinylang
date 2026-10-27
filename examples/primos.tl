# lista os primos até um limite usando divisão por tentativa

fn ehPrimo(n) {
    if (n < 2) { return false; }
    let d = 2;
    while (d * d <= n) {
        if (n % d == 0) { return false; }
        d = d + 1;
    }
    return true;
}

let limite = 50;
let saida = "";
let n = 2;
while (n <= limite) {
    if (ehPrimo(n)) { saida = saida + str(n) + " "; }
    n = n + 1;
}
print("primos até", limite, ":", saida);
