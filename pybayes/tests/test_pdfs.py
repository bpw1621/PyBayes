# Copyright (c) 2010 Matej Laitl <matej@laitl.cz>
# Distributed under the terms of the GNU General Public License v2 or any
# later version of the license, at your option.

"""Tests for pdfs"""

from copy import copy, deepcopy
from math import exp, log, sqrt

import numpy as np

import pybayes as pb
from support import PbTestCase


class TestRVComp(PbTestCase):
    """Test random variable component"""

    def test_init(self):
        rvcomp = pb.RVComp(123, "pretty name")
        self.assertEquals(rvcomp.name, "pretty name")
        self.assertEquals(rvcomp.dimension, 123)
        rvcomp = pb.RVComp(345)
        self.assertEquals(rvcomp.name, None)
        self.assertEquals(rvcomp.dimension, 345)

    def test_invalid_init(self):
        self.assertRaises(TypeError, pb.RVComp, 0.45)  # non-integer dimension
        self.assertRaises(TypeError, pb.RVComp, "not a number", "def")
        self.assertRaises(ValueError, pb.RVComp, 0)  # zero dimension should not be allowed
        self.assertRaises(ValueError, pb.RVComp, -1, "abc")
        self.assertRaises(TypeError, pb.RVComp, 1, 0.456)  # non-string name


class TestRV(PbTestCase):
    """Test random variable representation"""

    def setUp(self):
        self.test_comps = pb.RVComp(1, "a"), pb.RVComp(1, "b"), pb.RVComp(1, "c"), pb.RVComp(1, "d")

    def test_init(self):
        comp_a = pb.RVComp(1, "a")
        comp_b = pb.RVComp(2, "b")
        rv_1 = pb.RV(comp_a, comp_b)
        self.assertEquals(rv_1.name, "[a, b]")
        self.assertEquals(rv_1.dimension, 3)
        self.assertTrue(rv_1.contains(comp_a))
        self.assertTrue(rv_1.contains(comp_b))
        rv_2 = pb.RV(rv_1)
        self.assertEquals(rv_2.name, "[a, b]")
        self.assertEquals(rv_2.dimension, 3)
        self.assertTrue(rv_2.contains(comp_a))
        self.assertTrue(rv_2.contains(comp_b))

        empty_rv = pb.RV()
        self.assertEquals(empty_rv.dimension, 0)
        self.assertEquals(empty_rv.name, "[]")

    def test_invalid_init(self):
        self.assertRaises(TypeError, pb.RV, 0.46)

    def test_copy(self):
        """Test that shallow copying RV works as expected"""
        o = pb.RV(*self.test_comps)
        c = copy(o)
        self.assertTrue(id(o) != id(c))
        self.assertTrue(id(o.name) == id(c.name))
        self.assertTrue(id(o.dimension) == id(c.dimension))
        self.assertTrue(id(o.components) == id(c.components))

    def test_deepcopy(self):
        """Test that deep copying RV works as expected"""
        o = pb.RV(*self.test_comps)
        c = deepcopy(o)
        self.assertRVsEqualNotSame(o, c)

    def test_contains(self):
        a, b, c, d = self.test_comps
        rv = pb.RV(b, d)
        self.assertFalse(rv.contains(a))
        self.assertTrue(rv.contains(b))
        self.assertFalse(rv.contains(c))
        self.assertTrue(rv.contains(d))

    def test_contains_all(self):
        a, b, c, d = self.test_comps
        rv = pb.RV(a, b, c)
        self.assertTrue(rv.contains_all([a, b]))
        self.assertTrue(rv.contains_all([c, b]))
        self.assertTrue(rv.contains_all([b, a, c]))
        self.assertFalse(rv.contains_all([b, c, d]))
        self.assertFalse(rv.contains_all([d]))
        self.assertFalse(rv.contains_all([a, b, c, d]))

    def test_contains_any(self):
        a, b, c, d = self.test_comps
        rv = pb.RV(a, b, c)
        self.assertTrue(rv.contains_any([a, d]))
        self.assertTrue(rv.contains_any([b, d]))
        self.assertTrue(rv.contains_any([d, c]))
        self.assertFalse(rv.contains_any([d]))


class TestCpdf(PbTestCase):
    """Test abstract class CPdf"""

    def setUp(self):
        self.cpdf = pb.CPdf()

    def test_init(self):
        self.assertEqual(type(self.cpdf), pb.CPdf)

    def test_abstract_methods(self):
        # this test may fail due to bug in cython [1] that was fixed in 0.13.1
        # [1] http://trac.cython.org/cython_trac/ticket/583
        self.assertRaises(NotImplementedError, self.cpdf.shape)
        self.assertRaises(NotImplementedError, self.cpdf.cond_shape)
        self.assertRaises(NotImplementedError, self.cpdf.mean, np.array([0.]))
        self.assertRaises(NotImplementedError, self.cpdf.variance, np.array([0.]))
        self.assertRaises(NotImplementedError, self.cpdf.eval_log, np.array([0.]), np.array([0.]))
        self.assertRaises(NotImplementedError, self.cpdf.sample, np.array([0.]))


class TestPdf(PbTestCase):
    """Test partially abstract class Pdf"""

    def setUp(self):
        self.pdf = pb.Pdf()

    def test_init(self):
        self.assertEqual(type(self.pdf), pb.Pdf)

    def test_abstract_methods(self):
        # this test may fail due to bug in cython [1]
        # [1] http://trac.cython.org/cython_trac/ticket/583
        self.assertRaises(NotImplementedError, self.pdf.shape)
        self.assertRaises(NotImplementedError, self.pdf.mean)
        self.assertRaises(NotImplementedError, self.pdf.variance)
        self.assertRaises(NotImplementedError, self.pdf.eval_log, np.array([0.]))
        self.assertRaises(NotImplementedError, self.pdf.sample)

    def test_cond_shape(self):
        self.assertEqual(self.pdf.cond_shape(), 0)

class TestUniPdf(PbTestCase):
    """Test uniform pdf"""

    def setUp(self):
        self.uni = pb.UniPdf(np.array([-10.]), np.array([20.]))
        (self.a, self.b) = (np.array([0., -1., 2.]), np.array([1., 1., 4.]))
        self.multiuni = pb.UniPdf(self.a, self.b)

    def test_init(self):
        self.assertEqual(type(self.uni), pb.UniPdf)
        self.assertEqual(type(self.multiuni), pb.UniPdf)

    def test_invalid_init(self):
        self.assertRaises(ValueError, pb.UniPdf, np.zeros(5), np.array([1., 2., 3., -0.01, 3.]))  # b must be > a element-wise

    def test_rvs(self):
        self.assertEqual(self.uni.rv.dimension, 1)
        self.assertEqual(self.uni.cond_rv.dimension, 0)
        self.assertEqual(self.multiuni.rv.dimension, 3)
        self.assertEqual(self.multiuni.cond_rv.dimension, 0)

        a = pb.RVComp(2, "a")
        b = pb.RVComp(1, "b")
        test_uni = pb.UniPdf(np.array([0., -1., 2.]), np.array([1., 1., 4.]), pb.RV(a, b))
        self.assertTrue(test_uni.rv.contains(a))
        self.assertTrue(test_uni.rv.contains(b))

    def test_shape(self):
        self.assertEqual(self.uni.shape(), 1)
        self.assertEqual(self.multiuni.shape(), 3)

    def test_cond_shape(self):
        # these tests are redundant, as cond_shape() is implemented in Pdf, but wont hurt
        self.assertEqual(self.uni.cond_shape(), 0)
        self.assertEqual(self.multiuni.cond_shape(), 0)

    def test_mean(self):
        self.assertTrue(np.all(self.uni.mean() == np.array([5.])))
        self.assertTrue(np.all(self.uni.mean(None) == np.array([5.])))  # test also cond. variant
        self.assertTrue(np.all(self.multiuni.mean() == np.array([0.5, 0., 3.])))

    def test_variance(self):
        self.assertTrue(np.all(self.uni.variance() == np.array([75.])))
        self.assertTrue(np.all(self.uni.variance(None) == np.array([75.])))  # cond variant
        self.assertTrue(np.all(self.multiuni.variance() == np.array([1./12., 1./3., 1./3.])))

    def test_eval_log(self):
        self.assertEqual(self.uni.eval_log(np.array([-10.1])), float('-inf'))
        self.assertEqual(self.uni.eval_log(np.array([-10.1]), None), float('-inf'))  # cond variant
        self.assertEqual(self.uni.eval_log(np.array([12.547])), log(1./30.))
        self.assertEqual(self.uni.eval_log(np.array([12.547]), None), log(1./30.))  # cond variant
        self.assertEqual(self.uni.eval_log(np.array([-10.1])), float('-inf'))
        self.assertEqual(self.uni.eval_log(np.array([-10.1]), None), float('-inf'))  # cond variant

        (x, y, z) = (0.2, 0.8, 3.141592)  # this point belongs to multiuni's interval
        one_under = np.array([[-0.1, y, z],  # one of the values is lower
                             [x, -1.04, z],
                             [x, y, -3.975]])
        one_over = np.array([[1465.67, y, z],  # one of the values is greater
                             [x, 1.000456, z],
                             [x, y, 4.67]])
        self.assertEqual(self.multiuni.eval_log(np.array([x, y, z])), log(1./(1.*2*2)))
        for i in range(3):
            self.assertEqual(self.multiuni.eval_log(one_under[i]), float('-inf'))
            self.assertEqual(self.multiuni.eval_log(one_over[i]), float('-inf'))

    def test_sample(self):
        for i in range(100):
            sample = self.uni.sample()
            cond_sample = self.uni.sample(None)  # cond variant
            self.assertTrue(-10. <= sample[0] <= 20.)  # test sample is within bounds
            self.assertTrue(-10. <= cond_sample[0] <= 20.)  # also for conditional variant

        for i in range(100):
            sample = self.multiuni.sample()
            self.assertTrue(np.all(self.a <= sample))
            self.assertTrue(np.all(sample <= self.b))

    def test_samples(self):
        n = 10
        samples = self.uni.samples(n)
        self.assertEqual(samples.shape[0], n)
        for i in range(n):
            self.assertTrue(-10. <= samples[i,0] <= 20.)


class TestGaussPdf(PbTestCase):
    """Test Gaussian pdf"""

    def setUp(self):
        # constructor parameters:
        self.mean = np.array([1., 3., 9.])
        self.covariance = np.array([
            [1., 0., 0.],
            [0., 2., 0.],
            [0., 0., 3.]
        ])

        # expected values:
        self.variance = np.array([1., 2., 3.])  # diagonal elements of covariance
        self.shape = 3  # shape of random variable (and mean)

        self.gauss = pb.GaussPdf(self.mean, self.covariance)

    def test_init(self):
        self.assertEqual(type(self.gauss), pb.GaussPdf)

    def test_invalid_init(self):
        constructor = pb.GaussPdf

        # invalid mean and variance shape
        self.assertRaises(ValueError, constructor, np.array([[1], [2]]), self.covariance)
        self.assertRaises(ValueError, constructor, self.mean, np.array([1., 2., 3.,]))

        # non-rectangular variance, incompatible mean and variance, non-symmetric variance
        self.assertRaises(ValueError, constructor, self.mean, np.array([
            [1., 2.],
            [3., 4.],
            [5., 6.]
        ]))
        self.assertRaises(ValueError, constructor, self.mean, np.array([
            [1., 2.],
            [3., 4.]
        ]))
        self.assertRaises(ValueError, constructor, np.array([1, 2]), np.array([
            [1, 2],
            [3, 4]
        ]))

    def test_copy(self):
        """Test that copying GaussPdf works as expected"""
        o = self.gauss  # original
        c = copy(o)  # copy
        self.assertTrue(id(o) != id(c))
        self.assertTrue(id(o.mu) == id(c.mu))
        self.assertTrue(id(o.R) == id(c.R))
        self.assertTrue(id(o.rv) == id(c.rv))
        self.assertTrue(id(o.cond_rv) == id(c.cond_rv))

    def test_deepcopy(self):
        """Test that deep copying GaussPdf works as expected"""
        o = self.gauss  # original
        c = deepcopy(o)  # copy
        self.assertTrue(id(o) != id(c))
        self.assertArraysEqualNotSame(o.mu, c.mu)
        self.assertArraysEqualNotSame(o.R, c.R)
        self.assertRVsEqualNotSame(o.rv, c.rv)
        self.assertRVsEqualNotSame(o.cond_rv, c.cond_rv)

    def test_rvs(self):
        self.assertEqual(self.gauss.rv.dimension, 3)
        self.assertEqual(self.gauss.cond_rv.dimension, 0)

        a, b = pb.RVComp(2, "a"), pb.RVComp(1, "b")
        gauss_rv = pb.GaussPdf(self.mean, self.covariance, pb.RV(a, b))
        self.assertTrue(gauss_rv.rv.contains(a))
        self.assertTrue(gauss_rv.rv.contains(b))

        # invalid total rv dimension:
        c = pb.RVComp(2)
        self.assertRaises(ValueError, pb.GaussPdf, self.mean, self.covariance, pb.RV(a, c))

    def test_shape(self):
        self.assertEqual(self.gauss.shape(), self.shape)

    def test_mean(self):
        self.assertTrue(np.all(self.gauss.mean() == self.mean))

    def test_variance(self):
        # this test may fail due to bug in cython [1] that was fixed in 0.13.1
        # [1] http://trac.cython.org/cython_trac/ticket/583
        self.assertTrue(np.all(self.gauss.variance() == self.variance))

    def test_eval_log(self):
        x = np.array([0.])
        norm = pb.GaussPdf(np.array([0.]), np.array([[1.]]))
        expected = np.array([
            1.48671951473e-06,
            0.000133830225765,
            0.00443184841194,
            0.0539909665132,
            0.241970724519,
            0.398942280401,
            0.241970724519,
            0.0539909665132,
            0.00443184841194,
            0.000133830225765,
            1.48671951473e-06,
        ])
        for i in xrange(0, 11):
            x[0] = i - 5.
            res = exp(norm.eval_log(x))
            self.assertApproxEqual(res, expected[i])

        # same variance, non-zero mean:
        norm = pb.GaussPdf(np.array([17.9]), np.array([[1.]]))
        for i in xrange(0, 11):
            x[0] = i - 5. + 17.9
            res = exp(norm.eval_log(x))
            self.assertApproxEqual(res, expected[i])

        # non-unit variance:
        norm = pb.GaussPdf(np.array([0.]), np.array([[15.0]]))
        expected = np.array([
            0.044766420317807747,
            0.060428346749642113,
            0.076309057876818423,
            0.090148500118746672,
            0.099629500639377908,
            0.10300645387285032,
            0.099629500639377908,
            0.090148500118746672,
            0.076309057876818423,
            0.060428346749642113,
            0.044766420317807747,
        ])
        for i in xrange(0, 11):
            x[0] = (i - 5.)
            res = exp(norm.eval_log(x))
            self.assertApproxEqual(res, expected[i])

    def test_sample_uni(self):
        """Test GaussPdf.sample() mean and variance (univariate case). This test MAY FAIL ocassionally (but not often) - the probabibility of happening so is maintained low."""
        N = 500

        mean = np.array([124.6])
        cov = np.array([[0.7953]])
        samples = pb.GaussPdf(mean, cov).samples(N)
        emp = pb.EmpPdf(samples)

        fuzz = 0.2
        self.assertTrue(np.all(abs(emp.mean() - mean) <= fuzz))

        var, fuzz = cov.diagonal(), 0.2
        self.assertTrue(np.all(abs(emp.variance() - var) <= fuzz))

    def test_sample_multi(self):
        """Test GaussPdf.sample() mean and variance (multivariate case). This test MAY FAIL ocassionally (but not often) - the probabibility of happening so is maintained low."""
        N = 500

        mean = np.array([124.6, -1.5])
        cov = np.array([[0.7953, 0.], [0., 1.7]])
        samples = pb.GaussPdf(mean, cov).samples(N)
        emp = pb.EmpPdf(samples)

        fuzz = 0.2
        self.assertTrue(np.all(abs(emp.mean() - mean) <= fuzz))

        var, fuzz = cov.diagonal(), 0.3
        self.assertTrue(np.all(abs(emp.variance() - var) <= fuzz))


class LogNormPdf(PbTestCase):
    """Test log-normal pdf assuming that GaussPdf is correct"""

    def setUp(self):
        self.lognorm = pb.LogNormPdf(np.array([2.]), np.array([[0.3]]))

    def test_init(self):
        self.assertEqual(type(self.lognorm), pb.LogNormPdf)

    def test_invalid_init(self):
        constructor = pb.LogNormPdf

        # bad cov shape:
        self.assertRaises(ValueError, constructor, np.array([0.]), np.array([1.]))
        # non-positive cov:
        self.assertRaises(ValueError, constructor, np.array([0.]), np.array([[0.]]))
        # negative cov:
        self.assertRaises(ValueError, constructor, np.array([0.]), np.array([[-1.]]))

    def test_shape(self):
        self.assertEqual(self.lognorm.shape(), 1)

    def test_mean(self):
        self.assertApproxEqual(self.lognorm.mean(), np.array([8.5848583971779]))

    def test_variance(self):
        self.assertApproxEqual(self.lognorm.variance(), np.array([25.784521942338]))

    def test_eval_log(self):
        exp_results = np.array([
            [0.          ],  # eval in -1
            [0.          ],  # in 0
            [0.0009269427],  # in 1
            [0.0211410253],  # in 2
            [0.0626788779],  # ...
            [0.0972013339],
            [0.1129713216],
            [0.1129302247],
            [0.1035460884],
            [0.0900930786],
            [0.0758493660],
            [0.0625284607],
            [0.0508581369],
            [0.0410177842],
            [0.0329143093],
            [0.0263400001],
            [0.0210561877]
        ])

        x = np.zeros(1.)
        for i in range(17):
            x[0] = i - 1.
            self.assertApproxEqual(exp(self.lognorm.eval_log(x)), exp_results[i][0])

    def test_sample(self):
        """Test LogNormPdf.sample() mean and variance. This test MAY FAIL ocassionally (but not often) - the probabibility of happening so is maintained low."""
        N = 500  # number of samples
        samples = np.log(self.lognorm.samples(N))  # note the logarithm
        emp = pb.EmpPdf(samples)  # Emipirical pdf computes sample mean and variance for us

        mean, fuzz = 2., 0.2
        self.assertTrue(np.all(abs(emp.mean() - mean) <= fuzz))

        var, fuzz = 0.3, 0.1
        self.assertTrue(np.all(abs(emp.variance() - var) <= fuzz))


class TestEmpPdf(PbTestCase):
    """Test empirical pdf"""

    def setUp(self):
        particles = np.array([
            [1., 2., 23.67, 0.],
            [2., 4., 23.67, 1.],
            [3., 6., 23.67, 3.],
            [4., 8., 23.67, 6.],
        ])
        self.emp = pb.EmpPdf(particles)

    def test_shape(self):
        # there were an error where EmpPdf returned nr of particles, so we use
        # different data-set to detect such error
        particles = np.array([
            [1., 2.],
            [2., 4.],
            [3., 6.],
            [4., 8.],
        ])
        emp = pb.EmpPdf(particles)
        self.assertEqual(emp.shape(), 2)

    def test_mean(self):
        self.assertApproxEqual(self.emp.mean(), np.array([2.5, 5., 23.67, 2.5]))
        self.emp.weights = np.array([0., 0.5, 0.5, 0])  # set different weights
        self.assertApproxEqual(self.emp.mean(), np.array([2.5, 5., 23.67, 2.]))
        # test also normalisation:
        self.emp.weights = np.array([0., 14.7, 14.7, 0])
        self.emp.normalise_weights()
        self.assertApproxEqual(self.emp.mean(), np.array([2.5, 5., 23.67, 2.]))

    def test_variance(self):
        self.assertApproxEqual(self.emp.variance(), np.array([1.25, 5., 0., 5.25]))
        self.emp.weights = np.array([0., 0.5, 0.5, 0])  # set different weights
        self.assertApproxEqual(self.emp.variance(), np.array([0.25, 1., 0., 1.]))
        # test also normalisation:
        self.emp.weights = np.array([0., 0.255, 0.255, 0])
        self.emp.normalise_weights()
        self.assertApproxEqual(self.emp.mean(), np.array([2.5, 5., 23.67, 2.]))


class TestMarginalizedEmpPdf(PbTestCase):
    """Test marginalized empirical pdf"""

    def setUp(self):
        gausses = np.array([
            pb.GaussPdf(np.array([1., 2.]), np.array([[1., 0.], [0., 2.]])),
            pb.GaussPdf(np.array([-2., -1.]), np.array([[9., 0.], [0., 3.]])),
            pb.GaussPdf(np.array([-8., 5.]), np.array([[1., 0.5], [0.5, 1.]])),
        ], dtype=pb.GaussPdf)
        particles = np.array([
            [1., 2.],
            [2., 4.],
            [3., 6.],
        ])
        self.emp = pb.MarginalizedEmpPdf(gausses, particles)

    def test_shape(self):
        self.assertEqual(self.emp.shape(), 4)

    def test_mean(self):
        self.assertApproxEqual(self.emp.mean(), np.array([-3., 2., 2., 4.]))
        # set different weights:
        self.emp.weights = np.array([0., 0.5, 0.5])
        self.assertApproxEqual(self.emp.mean(), np.array([-5., 2., 2.5, 5.]))
        # test also normalisation:
        self.emp.weights = np.array([0., 14.7, 14.7])
        self.emp.normalise_weights()
        self.assertApproxEqual(self.emp.mean(), np.array([-5., 2., 2.5, 5.]))

    def test_variance(self):
        self.assertApproxEqual(self.emp.variance(), np.array([125./3., 32./3., 2./3., 8./3.]))
        # test different weights
        self.emp.weights = np.array([0., 0.5, 0.5])
        self.assertApproxEqual(self.emp.variance(), np.array([50., 14., 0.25, 1.]))
        # test also normalisation:
        self.emp.weights = np.array([0., 0.255, 0.255])
        self.emp.normalise_weights()
        self.assertApproxEqual(self.emp.variance(), np.array([50., 14., 0.25, 1.]))


class TestProdPdf(PbTestCase):
    """Test unconditional product of unconditional pdfs"""

    def setUp(self):
        self.uni = pb.UniPdf(np.array([0., 0.]), np.array([1., 2.]))
        self.gauss = pb.GaussPdf(np.array([0.]), np.array([[1.]]))
        self.prod = pb.ProdPdf((self.uni, self.gauss))

    def test_rvs(self):
        self.assertEqual(self.prod.rv.dimension, 3)

        # test that child rv components are copied into parent ProdPdf
        a, b, c = pb.RVComp(1, "a"), pb.RVComp(1, "b"), pb.RVComp(1, "c")
        uni = pb.UniPdf(np.array([0., 0.]), np.array([1., 2.]), pb.RV(a, b))
        gauss = pb.GaussPdf(np.array([0.]), np.array([[1.]]), pb.RV(c))
        prod = pb.ProdPdf((uni, gauss))

        self.assertEquals(prod.rv.name, "[a, b, c]")
        for rv_comp in a, b, c:
            self.assertTrue(prod.rv.contains(rv_comp))

        # that that custom rv passed to constructor is accepted
        d = pb.RVComp(3, "d")
        prod_custom = pb.ProdPdf((uni, gauss), pb.RV(d))
        self.assertEquals(prod_custom.rv.name, "[d]")
        self.assertTrue(prod_custom.rv.contains(d))
        self.assertFalse(prod_custom.rv.contains(a))
        self.assertFalse(prod_custom.rv.contains(b))
        self.assertFalse(prod_custom.rv.contains(c))

    def test_shape(self):
        self.assertEqual(self.prod.shape(), self.uni.shape() + self.gauss.shape())

    def test_mean(self):
        mean = self.prod.mean()
        self.assertTrue(np.all(mean[0:2] == self.uni.mean()))
        self.assertTrue(np.all(mean[2:3] == self.gauss.mean()))

    def test_variance(self):
        variance = self.prod.variance()
        self.assertTrue(np.all(variance[0:2] == self.uni.variance()))
        self.assertTrue(np.all(variance[2:3] == self.gauss.variance()))

    def test_eval_log(self):
        test_points = np.array([  # point we evaluate product in
            [-1., -1., 0.],
            [0.4, -1., 0.],
            [0.4, 1.7, 0.],
            [0.4, 2.1, 0.],
            [1.2, 2.1, 0.]
        ])
        p = exp(self.gauss.eval_log(np.array([0.]))) # = 1/sqrt(2*PI)
        exp_values = np.array([  # expected values. (not the logarithm of them)
            0.*p,  # 0*0*p
            0.*p,  # 1*0*p
            0.5*p,  # 1*0.5*p
            0.*p,  # 1*0*p
            0.*p,  # 0*0*p
        ])
        for i in range(test_points.shape[0]):
            val = exp(self.prod.eval_log(test_points[i]))
            self.assertEqual(val, exp_values[i])

    def test_sample(self):
        # we can only somehow test unifrom pdf, so we create a product of them
        uni_list = []
        for i in range(10):
            uni_list.append(pb.UniPdf(np.array([i+0.]), np.array([i+1.])))
        uni_prod = pb.ProdPdf(uni_list)  # a product of 10 UniPdfs
        for i in range(100):
            sample = uni_prod.sample()
            for j in range(10): # test each component..
                self.assertTrue(j <= sample[j] <= j + 1)  # ..is within bounds


class TestMLinGaussCPdf(PbTestCase):
    """Test conditional Gaussian pdf with mean as a linear function of cond"""

    def setUp(self):
        # constructor parameters:
        self.A = np.array([
            [1., 0.],
            [0., 2.],
            [-1., -1.]
        ])
        self.b = np.array([-0.5, -1., -1.5])
        self.covariance = np.array([
            [1., 0., 0.],
            [0., 2., 0.],
            [0., 0., 3.]
        ])

        # expected values:
        self.variance = np.array([1., 2., 3.])  # diagonal elements of covariance
        self.shape = 3  # shape of random variable (and mean)
        self.cond_shape = 2

        self.test_conds = np.array([  # array of test conditions (shared by various tests)
            [0., 0.],
            [1., 0.],
            [0., -1.],
        ])
        self.cond_means = np.array([  # array of mean values that match (first n entries of) test_conds
            self.b,
            np.array([1., 0., -1.]) + self.b,  # computed from self.A
            np.array([0., -2., 1.]) + self.b,  # computed from self.A
        ])

        self.gauss = pb.MLinGaussCPdf(self.covariance, self.A, self.b)

    def test_different_base_class(self):
        cov = np.array([[1.]])
        mean = np.array([-14.568])
        condlognorm = pb.MLinGaussCPdf(cov, np.array([[1.]]), np.array([0.]), base_class=pb.LogNormPdf)
        lognorm = pb.LogNormPdf(mean, cov)

        self.assertEqual(condlognorm.mean(mean), lognorm.mean())
        self.assertEqual(condlognorm.variance(mean), lognorm.variance())
        for x in np.array([[-0.4],[2.4],[4.5],[12.5]]):
            self.assertEqual(condlognorm.eval_log(x, mean), lognorm.eval_log(x))
        for i in range(30):
            # only test that samples are positive
            self.assertTrue(condlognorm.sample(mean)[0] >= 0)

    def test_init(self):
        self.assertEqual(type(self.gauss), pb.MLinGaussCPdf)

    def test_invalid_init(self):
        constructor = pb.MLinGaussCPdf

        # covariance not compatible with A, b:
        self.assertRaises(ValueError, constructor, np.array([[1.,0.],[0.,1.]]), self.A, self.b)
        # A not compatible with covariance:
        self.assertRaises(ValueError, constructor, self.covariance, np.array([[1.,0.],[0.,1.]]), self.b)
        # b not compatible with covariance:
        self.assertRaises(ValueError, constructor, self.covariance, self.A, np.array([1., 2.]))

    def test_rvs(self):
        self.assertEqual(self.gauss.rv.dimension, 3)
        self.assertEqual(self.gauss.cond_rv.dimension, 2)

        a, b, c, d = pb.RVComp(2, 'a'), pb.RVComp(1, 'b'), pb.RVComp(1, 'c'), pb.RVComp(1, 'd')
        rv = pb.RV(a, b)
        cond_rv = pb.RV(c, d)
        gauss = pb.MLinGaussCPdf(self.covariance, self.A, self.b, rv, cond_rv)
        self.assertTrue(gauss.rv.contains(a))
        self.assertTrue(gauss.rv.contains(b))
        self.assertFalse(gauss.rv.contains(c))
        self.assertFalse(gauss.rv.contains(d))

        self.assertFalse(gauss.cond_rv.contains(a))
        self.assertFalse(gauss.cond_rv.contains(b))
        self.assertTrue(gauss.cond_rv.contains(c))
        self.assertTrue(gauss.cond_rv.contains(d))

    def test_shape(self):
        self.assertEqual(self.gauss.shape(), self.shape)

    def test_cond_shape(self):
        self.assertEqual(self.gauss.cond_shape(), self.cond_shape)

    def test_mean(self):
        for i in range(self.cond_means.shape[0]):
            mean = self.gauss.mean(self.test_conds[i])
            self.assertTrue(np.all(mean == self.cond_means[i]))

    def test_variance(self):
        for i in range(self.test_conds.shape[0]):
            # test all test conditions, the result must not depend on it
            self.assertTrue(np.all(self.gauss.variance(self.test_conds[i]) == self.variance))

    def test_eval_log(self):
        x = np.array([0.])
        cond = np.array([0.])
        norm = pb.MLinGaussCPdf(np.array([[1.]]), np.array([[1.]]), np.array([-1.]))
        expected = np.array([
            1.48671951473e-06,
            0.000133830225765,
            0.00443184841194,
            0.0539909665132,
            0.241970724519,
            0.398942280401,
            0.241970724519,
            0.0539909665132,
            0.00443184841194,
            0.000133830225765,
            1.48671951473e-06,
        ])
        for i in xrange(0, 11):
            # cond is set to [1.], which should produce mean = [0.]
            x[0] = i - 5.
            cond[0] = 1.
            res = exp(norm.eval_log(x, cond))
            self.assertApproxEqual(res, expected[i])

            # cond is set to [456.78], which should produce mean = [455.78]
            x[0] = i - 5. + 455.78
            cond[0] = 456.78
            res = exp(norm.eval_log(x, cond))
            self.assertApproxEqual(res, expected[i])

    def test_sample(self):
        # Just test right dimension and shape for now
        for i in range(self.test_conds.shape[0]):
            x = self.gauss.sample(self.test_conds[i])
            self.assertEqual(x.ndim, 1)
            self.assertEqual(x.shape[0], self.covariance.shape[0])


class TestLinGaussCPdf(PbTestCase):
    """Test conditional Gaussian pdf with mean and cov as linear functions of cond"""

    def setUp(self):
        # constructor parameters:
        self.coeficients = (10., 5., 0.1, -1.)

        # array of test conditions (shared by various tests)
        self.test_conds = np.array([
            [-1., 20.],
            [0., 30.],
            [1., 11.],
        ])
        # array of mean values that match (first n entries of) test_conds
        self.cond_means = np.array([
            [-5.],
            [5.],
            [15.]
        ])
        # array of variance values that match (first n entries of) test_conds
        self.cond_vars = np.array([
            [1.],
            [2.],
            [0.1]
        ])

        self.gauss = pb.LinGaussCPdf(*self.coeficients)

    def test_init(self):
        self.assertEqual(type(self.gauss), pb.LinGaussCPdf)

    def test_invalid_init(self):
        constructor = pb.LinGaussCPdf

        self.assertRaises(TypeError, constructor, 1, 2, 3, 4)

    def test_different_base_class(self):
        cov = np.array([[1.]])
        mean = np.array([-14.568])
        cond = np.array([mean[0], cov[0,0]])
        condlognorm = pb.LinGaussCPdf(1., 0., 1., 0., base_class=pb.LogNormPdf)
        lognorm = pb.LogNormPdf(mean, cov)

        self.assertEqual(condlognorm.mean(cond), lognorm.mean())
        self.assertEqual(condlognorm.variance(cond), lognorm.variance())
        for x in np.array([[-0.4],[2.4],[4.5],[12.5]]):
            self.assertEqual(condlognorm.eval_log(x, cond), lognorm.eval_log(x))
        for i in range(30):
            # only test that samples are positive
            self.assertTrue(condlognorm.sample(cond)[0] >= 0)

    def test_rvs(self):
        self.assertEqual(self.gauss.rv.dimension, 1)
        self.assertEqual(self.gauss.cond_rv.dimension, 2)

        a, b, c = pb.RVComp(1, 'a'), pb.RVComp(1, 'b'), pb.RVComp(1, 'c')
        rv = pb.RV(a)
        cond_rv = pb.RV(b, c)
        gauss = pb.LinGaussCPdf(*self.coeficients, rv=rv, cond_rv=cond_rv)
        self.assertTrue(gauss.rv.contains(a))
        self.assertFalse(gauss.rv.contains(b))
        self.assertFalse(gauss.rv.contains(c))

        self.assertFalse(gauss.cond_rv.contains(a))
        self.assertTrue(gauss.cond_rv.contains(b))
        self.assertTrue(gauss.cond_rv.contains(c))

    def test_shape(self):
        self.assertEqual(self.gauss.shape(), 1)

    def test_cond_shape(self):
        self.assertEqual(self.gauss.cond_shape(), 2)

    def test_mean(self):
        for i in range(self.cond_means.shape[0]):
            mean = self.gauss.mean(self.test_conds[i])
            self.assertTrue(np.all(mean == self.cond_means[i]))

    def test_variance(self):
        for i in range(self.test_conds.shape[0]):
            variance = self.gauss.variance(self.test_conds[i])
            self.assertApproxEqual(variance, self.cond_vars[i])

    def test_eval_log(self):
        # for this test, we assume that GaussPdf is already well tested and correct
        for i in range(self.test_conds.shape[0]):
            cond = self.test_conds[i]
            mean = self.cond_means[i]
            var = self.cond_vars[i].reshape((1,1))
            gauss = pb.GaussPdf(mean, var)
            for j in range (-5, 6):
                x = mean + j*var[0]/2.
                ret = self.gauss.eval_log(x, cond)
                self.assertApproxEqual(ret, gauss.eval_log(x))

    def test_sample(self):
        """Test that 10 LinGaussCPdf samples are within mean +- n*sigma (>99.9% probability for n=3.3)"""
        n = 4
        for i in range(self.test_conds.shape[0]):
            cond = self.test_conds[i]
            mean = self.cond_means[i,0]
            sigma = sqrt(self.cond_vars[i,0])
            for j in range (10):
                sample = self.gauss.sample(cond)[0] - mean
                self.assertTrue(-n*sigma < sample < n*sigma)
        # TODO: one may also generate much more samples and calculate moments


class TestGaussCPdf(PbTestCase):
    """Test general gauss cpdf"""

    def setUp(self):
        def f(x):
            return -x
        self.f = f
        def g(x):
            return np.diag(-x)
        self.g = g
        self.cgauss = pb.GaussCPdf(2, 2, f, g)
        self.gauss = pb.GaussPdf(np.array([1., 2.]), np.array([[1., 0.], [0., 2.]]))
        self.cond = np.array([-1., -2.])  # condition that makes cgauss behave as gauss

    def test_different_base_class(self):
        condlognorm = pb.GaussCPdf(1, 1, self.f, self.g, base_class=pb.LogNormPdf)
        lognorm = pb.LogNormPdf(np.array([1.]), np.array([[1.]]))
        cond = np.array([-1.])  # makes condlognorm behave as lognorm

        self.assertEqual(condlognorm.mean(cond), lognorm.mean())
        self.assertEqual(condlognorm.variance(cond), lognorm.variance())
        for x in np.array([[-0.4],[2.4],[4.5],[12.5]]):
            self.assertEqual(condlognorm.eval_log(x, cond), lognorm.eval_log(x))
        for i in range(30):
            # only test that samples are positive
            self.assertTrue(np.all(condlognorm.sample(cond) >= 0))

    def test_mean(self):
        self.assertApproxEqual(self.cgauss.mean(self.cond), self.gauss.mean())

    def test_variance(self):
        self.assertApproxEqual(self.cgauss.variance(self.cond), self.gauss.variance())

    def test_eval_log(self):
        for i in range(15):
            x = np.array([i - 6.156, i - 4.7967])
            self.assertApproxEqual(self.cgauss.eval_log(x, self.cond), self.gauss.eval_log(x))

    def test_sample(self):
        """Test GaussCPdf.sample() mean and variance. This test MAY FAIL ocassionally (but not often) - the probabibility of happening so is maintained low."""
        N = 500  # number of samples
        samples = self.cgauss.samples(N, self.cond)
        emp = pb.EmpPdf(samples)  # Emipirical pdf computes sample mean and variance for us

        fuzz = np.array([0.3, 0.3])

        mean = self.cgauss.mean(self.cond)
        self.assertTrue(np.all(abs(emp.mean() - mean) <= fuzz))

        var = self.cgauss.variance(self.cond)
        self.assertTrue(np.all(abs(emp.variance() - var) <= fuzz))


class TestProdCPdf(PbTestCase):
    """Test conditional product of pdfs"""

    def setUp(self):
        ide = np.array([[1.]])  # 1x1 identity matrix
        self.gauss = pb.MLinGaussCPdf(ide, ide, np.array([0.]))
        self.uni = pb.UniPdf(np.array([0.]), np.array([2.]))
        self.prod = pb.ProdCPdf((self.gauss, self.uni))

    def test_init_with_rvs(self):
        x, y = pb.RVComp(1, "result"), pb.RVComp(1, "condition")
        self.uni.rv = pb.RV(y)
        self.gauss.cond_rv = pb.RV(y)
        self.gauss.rv = pb.RV(x)
        prod2 = pb.ProdCPdf((self.gauss, self.uni), pb.RV(x, y), pb.RV())

    def test_shape(self):
        self.assertEqual(self.prod.shape(), self.uni.shape() + self.gauss.shape())

    def test_cond_shape(self):
        self.assertEqual(self.prod.cond_shape(), 0)

    #def test_mean(self):
        #mean = self.prod.mean()
        #self.assertTrue(np.all(mean[0:2] == self.uni.mean()))
        #self.assertTrue(np.all(mean[2:3] == self.gauss.mean()))

    #def test_variance(self):
        #variance = self.prod.variance()
        #self.assertTrue(np.all(variance[0:2] == self.uni.variance()))
        #self.assertTrue(np.all(variance[2:3] == self.gauss.variance()))

    def test_eval_log(self):
        test_points = np.array([  # point we evaluate product in
            [-0.5, -0.5],
            [-0.5,  0.5],
            [-0.5,  1.5],
            [ 0.5, -0.5],
            [ 0.5,  0.5],
            [ 0.5,  1.5],
            [ 1.5, -0.5],
            [ 1.5,  0.5],
            [ 1.5,  1.5],
        ])

        for i in range(test_points.shape[0]):
            val = exp(self.prod.eval_log(test_points[i], np.array([])))
            expected = exp(self.gauss.eval_log(test_points[i,:1], test_points[i,1:])) * exp(self.uni.eval_log(test_points[i,1:]))
            self.assertApproxEqual(val, expected)

    def test_sample(self):
        for i in range(10):
            # this test is really dumb, but nothing better invented yet
            self.assertEqual(self.prod.sample(np.array([])).shape, (2,))
