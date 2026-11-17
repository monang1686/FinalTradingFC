"""Check that the standalone simulator remains parseable and exposes metrics."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

PAGE=Path(__file__).resolve().parents[1]/'experimental'/'simulator.html'

class SimulatorSmokeTests(unittest.TestCase):
    def test_controls_and_metrics_present(self):
        html=PAGE.read_text(encoding='utf-8')
        for element in ('capital','start','buy','sell','cash','profit','inventory','completed',
                        'wins','avg-roi','fees','holding-time','holdings','history','message',
                        'plan-buy','plan-profit','tick-mode','break-even','target-price','target-profit','target-roi'):
            self.assertIn('id="'+element+'"',html)
        self.assertIn('SOLO SIMULAZIONE',html)
        self.assertIn('Math.floor(x.value*95/100)',html)
        self.assertIn('trades.push',html)
        self.assertIn('function minSellPrice',html)
        self.assertIn('Math.floor(mid*95/100)',html)
        self.assertIn('function nextExamplePrice',html)
        self.assertIn('NON verificati per FC 27',html)

    @unittest.skipUnless(shutil.which('node'),'Node.js unavailable')
    def test_inline_javascript_syntax(self):
        html=PAGE.read_text(encoding='utf-8')
        scripts=re.findall(r'<script(?:\\s[^>]*)?>(.*?)</script>',html,re.S|re.I)
        self.assertEqual(len(scripts),1)
        result=subprocess.run(['node','--check','-'],input=scripts[0],text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__':
    unittest.main()
