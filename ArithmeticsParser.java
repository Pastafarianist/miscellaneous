import java.util.Locale;

public class ArithmeticsParser {

	static Tokenizer tk = null;

	public static void main(String[] args) {
		// Assuming that each argument contains a separate expression
		for (String expr : args) {
			double ans = evalExpr(expr);
			// Need US locale for decimal point instead of comma
			System.out.printf(Locale.US, "%.5f\n", ans);
		}
	}

	public static double evalExpr(String expr) {
		// Remove spaces & convert to uppercase
		String trimmed = expr.replaceAll(" ", "");
		String upper = trimmed.toUpperCase();
		// Run recursive descent
		tk = new Tokenizer(upper);
		tk.updateToken();
		return evalSum();
	}

	public static double evalSum() {
		// Parses series of additions/subtractions (lowest priority)
		double res = evalMult();
		while (true) {
			switch (tk.last_token) {
			case PLUS:
				tk.updateToken();
				res += evalMult();
				break;
			case MINUS:
				tk.updateToken();
				res -= evalMult();
				break;
			default:
				return res;
			}
		}

	}

	public static double evalMult() {
		// Parses series of multiplications/divisions (medium priority)
		double res = evalTightest();
		while (true) {
			switch (tk.last_token) {
			case MULT:
				tk.updateToken();
				res *= evalTightest();
				break;
			case DIV:
				tk.updateToken();
				res /= evalTightest();
				break;
			default:
				return res;
			}
		}
	}

	public static double evalTightest() {
		// Parses brackets, function applications and individual numbers
		// (highest priority)
		switch (tk.last_token) {
		case LB:
			return evalBrackets();
		case SIN:
			tk.updateToken();
			return Math.sin(evalBrackets());
		case COS:
			tk.updateToken();
			return Math.cos(evalBrackets());
		case EXP:
			tk.updateToken();
			return Math.exp(evalBrackets());
		case PI:
			tk.updateToken();
			return Math.PI;
		case E:
			tk.updateToken();
			return Math.E;
		case NUM:
			tk.updateToken();
			return tk.last_num;
		case MINUS:
			tk.updateToken();
			return -evalMult();
		default:
			throw new RuntimeException(String.format(
					"Did not expect token %s at position %d",
					tk.last_token.toString(), tk.pos));
		}
	}

	public static double evalBrackets() {
		// Helper function to parse brackets, i.e. function arguments
		tk.ensureToken(Tokenizer.Tokens.LB);
		tk.updateToken();
		double tmp = evalSum();
		tk.ensureToken(Tokenizer.Tokens.RB);
		tk.updateToken();
		return tmp;
	}

}

class Tokenizer {
	private String expr;
	public int pos;

	public Tokens last_token;
	public double last_num;

	public enum Tokens {
		LB, RB, PLUS, MINUS, MULT, DIV, SIN, COS, EXP, PI, E, NUM, END;
	}

	public Tokenizer(String expr) {
		this.expr = expr;
		this.pos = 0;
		this.last_token = null;
		this.last_num = Double.NaN;
	}

	public void updateToken() {
		last_token = null;
		if (pos == expr.length()) {
			last_token = Tokens.END;
			return;
		}
		switch (expr.charAt(pos)) {
		case '(':
			pos++;
			last_token = Tokens.LB;
			return;
		case ')':
			pos++;
			last_token = Tokens.RB;
			return;
		case '+':
			pos++;
			last_token = Tokens.PLUS;
			return;
		case '-':
			pos++;
			last_token = Tokens.MINUS;
			return;
		case '*':
			pos++;
			last_token = Tokens.MULT;
			return;
		case '/':
			pos++;
			last_token = Tokens.DIV;
			return;
		}
		if (Character.isDigit(expr.charAt(pos))) {
			last_num = parseNumber();
			last_token = Tokens.NUM;
			return;
		}
		if (Character.isLetter(expr.charAt(pos))) {
			String word = parseWord();
			last_token = Tokens.valueOf(word);
			return;
		}
		throw new RuntimeException(String.format(
				"Unrecognized token at position %d", pos));
	}

	private double parseNumber() {
		int pos_end = pos;
		String num = null;
		while (pos_end < expr.length()
				&& Character.isDigit(expr.charAt(pos_end))) {
			pos_end++;
		}
		if (pos_end == expr.length()) {
			num = expr.substring(pos, pos_end);
		} else if (expr.charAt(pos_end) == '.') {
			pos_end++;
			while (pos_end < expr.length()
					&& Character.isDigit(expr.charAt(pos_end))) {
				pos_end++;
			}
			num = expr.substring(pos, pos_end);
		} else {
			num = expr.substring(pos, pos_end);
		}
		pos = pos_end;
		return Double.parseDouble(num);
	}

	private String parseWord() {
		int pos_end = pos;
		while (pos_end < expr.length()
				&& Character.isLetter(expr.charAt(pos_end))) {
			pos_end++;
		}
		String res = expr.substring(pos, pos_end);
		pos = pos_end;
		return res;
	}

	public void ensureToken(Tokens tok) {
		if (last_token != tok) {
			throw new RuntimeException(String.format(
					"Unexpected token at position %d: expected %s, found %s",
					pos, tok.toString(), last_token.toString()));
		}
	}
}