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


class TestLayer2Sheaf:
    def test_29_sheaf_h1(self, driver):
        load_and_run(driver)
        h1 = js(driver, "return results.sheaf.h1")
        assert h1 >= 0

    def test_30_sheaf_consistency(self, driver):
        cr = js(driver, "return results.sheaf.consistency_ratio")
        assert 0 <= cr <= 1

class TestLayer2Ricci:
    def test_31_ricci_curvatures(self, driver):
        load_and_run(driver)
        n = js(driver, "return results.ricci.edgeCurvatures.length")
        assert n > 0

    def test_32_ricci_avg_finite(self, driver):
        avg = js(driver, "return results.ricci.avgCurvature")
        assert abs(avg) < 10

    def test_33_ricci_svg(self, driver):
        html = js(driver, "return document.getElementById('ricciContainer').innerHTML")
        assert '<svg' in html.lower()

class TestLayer2InfoGeom:
    def test_34_frechet_mean(self, driver):
        load_and_run(driver)
        mu = js(driver, "return results.infoGeom.frechetMean.mu")
        assert mu is not None and abs(mu) < 10

    def test_35_scalar_curvature_negative(self, driver):
        sc = js(driver, "return results.infoGeom.scalarCurvature")
        assert sc < 0, "Normal family scalar curvature must be negative"

    def test_36_geodesic_var_positive(self, driver):
        gv = js(driver, "return results.infoGeom.geodesicVar")
        assert gv >= 0

    def test_37_info_geom_svg(self, driver):
        html = js(driver, "return document.getElementById('infoGeomContainer').innerHTML")
        assert '<svg' in html.lower()

class TestLayer2Morse:
    def test_38_density_computed(self, driver):
        load_and_run(driver)
        n = js(driver, "return results.morse.density.length")
        assert n > 50

    def test_39_critical_points(self, driver):
        nMax = js(driver, "return results.morse.maxima.length")
        assert nMax >= 1, "Must have at least 1 peak"

    def test_40_morse_svg(self, driver):
        html = js(driver, "return document.getElementById('morseContainer').innerHTML")
        assert '<svg' in html.lower()

class TestLayer2Kolmogorov:
    def test_41_lz_complexity(self, driver):
        load_and_run(driver)
        lz = js(driver, "return results.kolmogorov.lzComplexity")
        assert lz >= 1

    def test_42_compressibility_bounded(self, driver):
        c = js(driver, "return results.kolmogorov.compressibility")
        assert -1 <= c <= 1

    def test_43_symbols_match_studies(self, driver):
        n = js(driver, "return results.kolmogorov.symbols.length")
        assert n == 16

class TestLayer2NoErrors:
    def test_44_all_datasets_layer2(self, driver):
        for ds in ['vitamind', 'hrt', 'homeopathy']:
            load_and_run(driver, ds)
            assert js(driver, "return results.sheaf !== null")
            assert js(driver, "return results.ricci !== null")
            assert js(driver, "return results.morse !== null")

    def test_45_no_severe_errors(self, driver):
        load_page(driver)
        logs = driver.get_log("browser")
        severe = [l for l in logs if l.get("level") == "SEVERE" and "favicon" not in l.get("message","").lower()]
        assert len(severe) == 0, f"JS errors: {severe}"


class TestLayer3Quantum:
    def test_46_von_neumann_nonneg(self, driver):
        load_and_run(driver)
        vn = js(driver, "return results.quantum.vonNeumann")
        assert vn >= 0

    def test_47_coherence_bounded(self, driver):
        c = js(driver, "return results.quantum.coherence")
        assert 0 <= c <= 1.5

    def test_48_entanglement(self, driver):
        ee = js(driver, "return results.quantum.entanglementEntropy")
        assert ee >= 0

class TestLayer3Category:
    def test_49_colimit_finite(self, driver):
        load_and_run(driver)
        mu = js(driver, "return results.category.colimit.mu")
        assert abs(mu) < 10

    def test_50_nat_trans_norm(self, driver):
        n = js(driver, "return results.category.natTransNorm")
        assert n >= 0

    def test_51_kan_extension(self, driver):
        ke = js(driver, "return Object.keys(results.category.kanExtension).length")
        assert ke >= 1

class TestLayer3Tropical:
    def test_52_tropical_mean(self, driver):
        load_and_run(driver)
        tm = js(driver, "return results.tropical.tropicalMean")
        assert tm is not None

    def test_53_tropical_rank(self, driver):
        tr = js(driver, "return results.tropical.tropRank")
        assert tr >= 1

class TestLayer3Padic:
    def test_54_padic_diameter(self, driver):
        load_and_run(driver)
        d = js(driver, "return results.padic.diameter")
        assert d >= 0

    def test_55_valuation_groups(self, driver):
        vg = js(driver, "return results.padic.nValGroups")
        assert vg >= 1

class TestLayer3NCGeom:
    def test_56_spectral_dim(self, driver):
        load_and_run(driver)
        sd = js(driver, "return results.ncGeom.spectralDim")
        assert sd > 0

    def test_57_dixmier_trace(self, driver):
        dt = js(driver, "return results.ncGeom.dixmierTrace")
        assert dt >= 0

class TestAllLayers:
    def test_58_all_datasets_all_layers(self, driver):
        for ds in ['vitamind', 'hrt', 'homeopathy']:
            load_and_run(driver, ds)
            for key in ['quantum', 'category', 'tropical', 'padic', 'ncGeom']:
                assert js(driver, f"return results.{key} !== null && results.{key} !== undefined"), f"{key} null for {ds}"

    def test_59_no_errors_final(self, driver):
        load_page(driver)
        logs = driver.get_log("browser")
        severe = [l for l in logs if l.get("level") == "SEVERE" and "favicon" not in l.get("message","").lower()]
        assert len(severe) == 0

    def test_60_total_modules(self, driver):
        """Verify all 17 modules produce results."""
        load_and_run(driver)
        keys = js(driver, "return Object.keys(results)")
        assert len(keys) == 17, f"Expected 17 modules, got {len(keys)}: {keys}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
