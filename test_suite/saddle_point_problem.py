"""
Interface Class for the Saddle Point Problem
"""
from __future__ import print_function, division
from scipy.optimize import basinhopping, differential_evolution
import numpy as np
from minimizers.cmaes import CMAES
import warnings


class SaddlePointProblem(object):
    def __init__(self, D_x, D_y):
        self._D_x = D_x
        self._D_y = D_y
        self._run = 0
        self._num_fevals = 0
        self._x_opt = None
        self._y_opt = None

    def get_x_opt(self):
        if self._x_opt is None:
            raise Exception("saddle point solution is not known, this function should not be called for this problem")
        else:
            return self._x_opt.copy()

    def get_y_opt(self):
        if self._y_opt is None:
            raise Exception("saddle point solution is not known, this function should not be called for this problem")
        else:
            return self._y_opt.copy()

    def evaluate(self, x, y, is_log=True):
        """ Evaluate the solutionx x and y. This is a wrapper for the
            rest of the functions that do preprocessing and evaluating the actual function.
            This is the function to be called by the solver
        :param x: D_x dimensional point in the unit cube
        :param y: D_y dimensional point in the unit cube
        :param is_log: flag to count the function call as part of the number of evaluations
        :return: objective function value
        """
        f_val = self._call_fct(x, y)

        if is_log:
            self._num_fevals += 1

        return f_val

    def _worst(self, x0, y0):
        """
        Return the worst value of the function given x0, i.e., max_y l(x0, y)
        y0 serves as an initial guess to start the search
        :param x0:
        :param y0:
        :return:
        """
        f_y = lambda y: - self.evaluate(x0, y)

        ret = basinhopping(f_y, x0=y0, minimizer_kwargs={'bounds': [(0, 1)] * self._D_y})
        f_worst = - ret.fun

        res = CMAES(f_y, y0.shape[0], x0=y0, is_restart=True, max_fevals=1e3).run()
        f_worst = max(-res[1], f_worst)

        # use DE
        ret = differential_evolution(f_y, bounds=[(0, 1)] * self._D_y)
        f_worst = max(-ret.fun, f_worst)

        return f_worst

    def relative_robustness(self, x0, y0):
        """
        Measure the robustness of x as y is tuned to maximize the objective function
        :return: the percentage change in the function value
        """
        assert (self._D_x == x0.shape[0]) and (len(x0.shape) == 1), "Invalid dimensions"
        assert (self._D_y == y0.shape[0]) and (len(y0.shape) == 1), "Invalid dimensions"
        f_0 = self.evaluate(x0, y0)
        f_worst = self._worst(x0, y0)

        robustness = (f_worst - f_0) / (abs(f_0) + np.finfo(np.float32).eps)
        assert robustness >= 0, "Maximizing worst-case returned a value better than the present worse: >= is expected"

        return robustness

    def relative_loss(self, x0, y0):
        """
            Measure the relative loss w.r.t. to the saddle point's objective value
            i.e.,  max(0, l(x0,y0) - l(x*,y*) / |l(x*,y*)|) as y0 does not necessary correspond to x0's worst solution
            This requires the knowledge of where the saddle point is, which is problem dependent
        :param x0:
        :param y0:
        :return:
        """
        if self._x_opt is None:
            raise Exception("saddle point solution is not known, this metric cant be computed")
        else:
            f_0 = self._call_fct(x0, y0)

            # x_opt, y_opt is in the origianl space
            f_opt = self._fct(self._x_opt, self._y_opt)

            loss = (f_0 - f_opt) / (abs(f_opt) + np.finfo(np.float32).eps)
            if loss < 0:
                warnings.warn(
                    'function value at ({x0},{y0}) is less than the saddle-pt value, is this a true minmax?'.format(
                        x0=x0,
                        y0=y0))

            return max(0, loss)

    def mse(self, x0, y0):
        """
            Measure the mse of (x0, x*) and (y0, y*)
            This requires the knowledge of where the saddle point is, which is problem dependent
        :param x0:
        :param y0:
        :return:
        """
        if self._x_opt is None or self._y_opt is None:
            raise Exception("saddle point solution is not known, this metric cant be computed")
        else:
            x0_mse = np.mean((self.get_unit_x_opt() - x0) ** 2)
            y0_mse = np.mean((self.get_unit_y_opt() - y0) ** 2)

            return x0_mse, y0_mse

    def regret(self, x0, y0):
        """
            Measure the regret that is max_y l(x_0, y) - l(x*,y*)
            y0 serves as an initial guess for solving maximizing l(x_0,y)
            This requires the knowledge of where the saddle point is, which is problem dependent
        :param x0: D_x numpy array
        :param y0: D_y numpy array
        :return:
        """
        if self._x_opt is None or self._y_opt is None:
            raise NotImplemented("This is problem-dependent, knowledge about the saddle point is required")
        else:
            return max(0, self._worst(x0, y0) - self._fct(self._x_opt, self._y_opt))

    def _call_fct(self, x, y):
        """ This function preprocess x and y before calling the `_fct`
            it is used as sometimes the domain of the `_fct` is not the unit cube.
        :param x: D_x dimensional point in the unit cube
        :param y: D_y dimensional point in the unit cube
        :return:
        """
        raise NotImplementedError("Inheriting classes should implement this method")

    def _fct(self, x, y):
        raise NotImplementedError("Inheriting classes should implement this method")

    def next_run(self):
        self._run += 0
        self._num_fevals = 0

    def get_run(self):
        return self._run

    def get_num_fevals(self):
        return self._num_fevals
