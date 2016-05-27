res <- read.table('../original_results/section_v_e_anytime_problem7_results.csv', header=TRUE, sep=',')

min_obj = min(min(res$qos, res$freecycles))
max_obj = max(max(res$qos, res$freecycles))

xlimits = c(min(res$timeout), max(res$timeout))
ylimits = c(min_obj, max_obj)

pdf('problem7.pdf')
fs = 1.5
fs_leg = 1.25

plot(res$timeout[res$method=="minizinc"], res$qos[res$method=="minizinc"], 
	xlim=xlimits,ylim=ylimits, type='b', pch='+', xlab='Time (s)', ylab='Normalised Objective Value',
	cex.lab=fs, cex.axis=fs, cex.main=fs, cex.sub=fs)
#, main='Problem 7: Anytime Algorithms')
lines(res$timeout[res$method=="minizinc"], res$freecycles[res$method=="minizinc"], pch='+', type='b', lty=2)

lines(res$timeout[res$method=="local"], res$qos[res$method=="local"], type='b', pch='o')
lines(res$timeout[res$method=="local"], res$freecycles[res$method=="local"], type='b', pch='o', lty=2)

x_pos = max(res$timeout) * 0.6
y_pos = max_obj * 0.75

legend(legend=c('Minizinc QoS', 'MiniZinc Util', 'Local Search QoS', 'Local Search Util'), 
	x=x_pos, y=y_pos, lty=c(1,2,1,2), pch=c('+','+','o','o'), cex=fs_leg)

dev.off()