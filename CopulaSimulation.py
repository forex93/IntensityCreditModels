from Copula import *
from CDS import *
from MarketData import *
from Calibration import *
from scipy.stats import scoreatpercentile
from numpy import arange, linspace
import csv


#------------------------------------------------------------------------------

class CopulaSimulation(object):
    """docstring for VaRSimulation"""
    def __init__(self, copula):
        self.copula = copula
        
    def Simulation(self, N):
        """docstring for Simulation"""
        results = []
        for i in range(N):
            taus = self.copula.Simulate()
            results.append(taus)
            # print taus
            
        return results
        
    def PortfolioLoss(self, simulation_results, t):
        """docstring for PortfolioLoss"""
        losses = []
        size = float(len(simulation_results[0]))
        for taus in simulation_results:
            loss = sum([1 if tau < t else 0 for tau in taus]) / size
            losses.append(loss)
        
        return losses
        
    def VaR(self, results, t, limit = 0.95):
        """docstring for VaR"""
        # print results[0]
        losses = self.PortfolioLoss(results, t)
        # print losses
        return scoreatpercentile(losses, limit)
    
#------------------------------------------------------------------------------

def FlatCorrelationMatrix(rho, N):
    """docstring for FlatCorrelationMatrix"""
    return rho * ones([N, N]) + (1 - rho) * eye(N, N)

# print FlatCorrelationMatrix(0.5, 10)

#------------------------------------------------------------------------------

def SimulatedVaRCurve(cds_class, market_data, copula_class, rho, size, n_simulations):
    """docstring for VaR"""
    if cds_class == HPCreditDefaultSwap:
        guess = [0.01]
    else:
        guess = [0.3, 0.8, 5, 0.02]
        
    calib = Calibration(    DiscountCurve   = FlatDiscountCurve(r = 0.02), 
                            MarketData      = market_data,
                            CDS             = cds_class,
                            Guess           = guess,
                            )
    calib.Calibrate()
    calibrated_gamma = calib.calibrated_gamma 
    CDS = cds_class()
    cov = FlatCorrelationMatrix(rho, size)

    copula = copula_class(CDS, calibrated_gamma, cov, size)
    CopSim = CopulaSimulation(copula)
    sim_results = CopSim.Simulation(n_simulations)
    print "Sim Results"
    # print sim_results
    print "Testing", CopSim.VaR(sim_results, 50)
    var_t = linspace(0, 50, 100)
    f = lambda x: CopSim.VaR(sim_results, x)
    var_v = map(f, var_t)
    return var_v

def SimulatedDefaultTimes(cds_class, market_data, copula_class, rho, size, n_simulations):
    """docstring for SimulatedDefault"""
    if cds_class == HPCreditDefaultSwap:
        guess = [0.01]
    else:
        guess = [0.3, 0.8, 5, 0.02]
        
    calib = Calibration(    DiscountCurve   = FlatDiscountCurve(r = 0.02), 
                            MarketData      = market_data,
                            CDS             = cds_class,
                            Guess           = guess,
                            )
    calib.Calibrate()
    calibrated_gamma = calib.calibrated_gamma 
    CDS = cds_class()
    cov = FlatCorrelationMatrix(rho, size)

    copula = copula_class(CDS, calibrated_gamma, cov, size)
    CopSim = CopulaSimulation(copula)
    sim_results = CopSim.Simulation(n_simulations)
    
    return sim_results
    
def CreateVaRTermStructure(rho, copula):
    """docstring for F"""
    spreads = { 'Date' : '17/5/10', 
                '1' : '350', 
                '2' : '350', 
                '5' : '400', 
                '7' : '450', 
                '10' : '600' 
                }
    data = MarketData(spreads)


    hp = SimulatedVaRCurve( HPCreditDefaultSwap, 
                            data, 
                            copula, 
                            rho, 
                            100, 
                            2000)

    gou = SimulatedVaRCurve(GammaOUCreditDefaultSwap, 
                            data, 
                            copula, 
                            rho, 
                            100, 
                            2000)
    # print res

    igou = SimulatedVaRCurve(IGOUCreditDefaultSwap, 
                            data, 
                            copula, 
                            rho, 
                            100, 
                            2000)
    # print res
    # cir = SimulatedVaRCurve(CIRCreditDefaultSwap, 
    #                         data, 
    #                         GaussianCopula, 
    #                         0.5, 
    #                         50, 
    #                         1000)

    headers = ["HP", "G-OU", "IG-OU"]
    values = zip(hp, gou, igou)
    rows_to_write = [headers]
    rows_to_write.extend(values)
    
    print_mapping = {   GaussianCopula : "GaussianCopula",
                        StudentTCopula : "StudentTCopula"
                        }
    
    filename = "Copulas/" + print_mapping[copula] + str(rho) + ".csv"
    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(rows_to_write)
        
if __name__ == '__main__':
    for rho in [0.8]:
        CreateVaRTermStructure(rho, StudentTCopula)
    
    
