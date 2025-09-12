import edu.princeton.cs.algs4.StdIn;
import edu.princeton.cs.algs4.StdOut;

public class HelloGoodbye {
    public static void main(String[] args) {
        String name1, name2;
        name1 = StdIn.readString();
        name2 = StdIn.readString();
        String s = "Hello " + name2 + " and " + name1 + '.';
        StdOut.println(s);
    }
}
