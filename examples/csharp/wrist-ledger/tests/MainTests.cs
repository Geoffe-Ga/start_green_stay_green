using Xunit;

namespace WristLedger.Tests
{
    /// <summary>
    /// Tests for wrist-ledger main entry point
    /// </summary>
    public class MainTests
    {
        [Fact]
        public void MainRuns_WithoutError()
        {
            // Test that Main method exists and can be called
            // This verifies the Hello World entry point compiles correctly
            var exception = Record.Exception(() =>
            {
                Program.Main(new string[] {});
            });

            Assert.Null(exception);
        }

        [Fact]
        public void MainMethod_Exists()
        {
            // Verify Main method exists in Program class
            var method = typeof(Program).GetMethod("Main");
            Assert.NotNull(method);
        }
    }
}
