 
pdf('problem_7_reps.pdf')
res <- read.table('../original_results/section_v_e_anytime_problem7_reps_results.csv', header=TRUE, sep=',')
fs = 1.5
boxplot(res$qos~res$timeout,data=res, xlab='Time (s)', ylab='Normalised QoS', cex.lab=fs, cex.axis=fs, cex.main=fs, cex.sub=fs)
dev.off()