import edu.princeton.cs.algs4.StdIn;
import edu.princeton.cs.algs4.StdOut;
import edu.princeton.cs.algs4.StdRandom;

public class RandomWord {
    public static void main(String[] args) {
        String s;
        int n = 0;
        while (!StdIn.isEmpty()) {
            n++;
            if (StdRandom.bernoulli(1.0 / n)) {
                s = StdIn.readString();
            }
        }
        StdOut.println(s);
    }
}
