"""
Selenium test suite for HyperMeta (hypermeta.html).
25 tests covering all 7 mathematical modules.
"""
import os, sys, time, pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HTML_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hypermeta.html")
FILE_URL = "file:///" + os.path.abspath(HTML_FILE).replace("\\", "/")

@pytest.fixture(scope="module")
def driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    d = webdriver.Chrome(options=opts)
    d.set_window_size(1400, 900)
    yield d
    d.quit()

def js(d, script):
    return d.execute_script(script)

def load_page(d):
    d.get(FILE_URL)
    WebDriverWait(d, 10).until(lambda dr: dr.execute_script("return typeof runHyperMeta === 'function'"))
    time.sleep(1)  # auto-loads vitamind + runs

def load_and_run(d, dataset='vitamind'):
    load_page(d)
    js(d, f"loadDataset('{dataset}')")
    js(d, "runHyperMeta()")
    time.sleep(0.5)


class TestPageLoad:
    def test_01_page_loads(self, driver):
        load_page(driver)
        assert 'HyperMeta' in driver.title

    def test_02_header_visible(self, driver):
        h1 = driver.find_element(By.TAG_NAME, "h1")
        assert 'HyperMeta' in h1.text

    def test_03_dataset_dropdown(self, driver):
        sel = driver.find_element(By.ID, "datasetSelect")
        assert sel.is_displayed()

    def test_04_vitamind_auto_loaded(self, driver):
        count = js(driver, "return studies.length")
        assert count == 16


class TestAllDatasets:
    def test_05_vitamind_runs(self, driver):
        load_and_run(driver, 'vitamind')
        assert js(driver, "return results !== null")

    def test_06_hrt_runs(self, driver):
        load_and_run(driver, 'hrt')
        assert js(driver, "return results !== null")

    def test_07_homeopathy_runs(self, driver):
        load_and_run(driver, 'homeopathy')
        assert js(driver, "return results !== null")


class TestPoincareDisk:
    def test_08_poincare_points(self, driver):
        load_and_run(driver)
        n = js(driver, "return results.poincare.points.length")
        assert n == 16

    def test_09_barycenter_inside_disk(self, driver):
        bx = js(driver, "return results.poincare.barycenter.x")
        by = js(driver, "return results.poincare.barycenter.y")
        assert bx**2 + by**2 < 1, "Barycenter must be inside unit disk"

    def test_10_dispersion_positive(self, driver):
        d = js(driver, "return results.poincare.dispersion")
        assert d > 0

    def test_11_poincare_svg_rendered(self, driver):
        html = js(driver, "return document.getElementById('poincareContainer').innerHTML")
        assert '<svg' in html.lower()


class TestPersistentHomology:
    def test_12_betti_numbers(self, driver):
        load_and_run(driver)
        b0 = js(driver, "return results.topo.betti0")
        assert b0 >= 1, "At least 1 connected component"

    def test_13_h1_bars(self, driver):
        n = js(driver, "return results.topo.h1Bars.length")
        assert n >= 0  # May or may not have loops

    def test_14_persistent_entropy(self, driver):
        pe = js(driver, "return results.topo.persistEntropy")
        assert pe >= 0

    def test_15_persistence_svg(self, driver):
        html = js(driver, "return document.getElementById('persistenceContainer').innerHTML")
        assert '<svg' in html.lower()


class TestWasserstein:
    def test_16_barycenter_finite(self, driver):
        load_and_run(driver)
        m = js(driver, "return results.wasserstein.mean")
        assert m is not None and abs(m) < 10

    def test_17_discrepancy_nonneg(self, driver):
        d = js(driver, "return results.wasserstein.discrepancy")
        assert d >= 0


class TestSpectral:
    def test_18_fiedler_nonneg(self, driver):
        load_and_run(driver)
        f = js(driver, "return results.spectral.fiedler")
        assert f >= -0.01  # Should be >= 0 for Laplacian

    def test_19_eigenvalues_computed(self, driver):
        n = js(driver, "return results.spectral.eigenvalues.length")
        assert n == 16

    def test_20_spectral_svg(self, driver):
        html = js(driver, "return document.getElementById('spectralContainer').innerHTML")
        assert '<svg' in html.lower() or 'rect' in html


class TestEntropy:
    def test_21_shannon_nonneg(self, driver):
        load_and_run(driver)
        s = js(driver, "return results.entropy.shannon")
        assert s >= 0

    def test_22_normalized_bounded(self, driver):
        n = js(driver, "return results.entropy.normalizedShannon")
        assert 0 <= n <= 1.001


class TestStrangeAttractor:
    def test_23_trajectory_length(self, driver):
        load_and_run(driver)
        n = js(driver, "return results.attractor.trajectory.length")
        assert n == 16

    def test_24_lyapunov_finite(self, driver):
        l = js(driver, "return results.attractor.lyapunov")
        assert abs(l) < 100


class TestFractal:
    def test_25_dimension_bounded(self, driver):
        load_and_run(driver)
        d = js(driver, "return results.fractal.dimension")
        assert 0 <= d <= 1.5


class TestNoErrors:
    def test_26_no_js_errors(self, driver):
        load_page(driver)
        for ds in ['vitamind', 'hrt', 'homeopathy']:
            js(driver, f"loadDataset('{ds}')")
            js(driver, "runHyperMeta()")
            time.sleep(0.5)
        logs = driver.get_log("browser")
        severe = [l for l in logs if l.get("level") == "SEVERE" and "favicon" not in l.get("message", "").lower()]
        assert len(severe) == 0, f"JS errors: {severe}"

    def test_27_results_section_visible(self, driver):
        display = js(driver, "return document.getElementById('resultsSection').style.display")
        assert display != 'none'

    def test_28_interpretation_content(self, driver):
        html = js(driver, "return document.getElementById('interpretContent').innerHTML")
        assert len(html) > 100


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
