import glob
import os
import time
from os.path import join

import matplotlib.pyplot as plt
import numpy as np
import pencil as pc
from matplotlib import markers
from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter as gf

lstyle = ["-", "--", "-.", ":", "+", "*", "x", "."]
lm = []
for marker in markers.MarkerStyle.markers:
    lm.append(marker)
lm = lm[:-16]
lm.remove(",")
lm.remove("_")
lm.remove("|")
cl = [
    "#003399",
    "#009900",
    "#990000",
    "#009999",
    "#990099",
    "#505505",
    "#999900",
    "#090090",
]

avkeys = ["bxmz", "bymz"]
avkeys = [
    "ruxmz",
    "ruymz",
    "ruzmz",
    "ekinmz",
    "rhomz",
    "uxmz",
    "uymz",
    "uzmz",
    "oumz",
    "jbmz",
    "oxmz",
    "oymz",
    "ozmz",
    "bxmz",
    "bymz",
    "jxmz",
    "jymz",
]
figsize = [2.8 * 1.61803, 2.8]
avfigsize = [4.0 * 1.61803, 2.0]
lfigsize = [3.25 * 1.61803, 3.0]
fontsize = 10

wrkdir = "."
simsdir = join("/scratch/project_462000509")
lpdf = False
if lpdf:
    png = ".pdf"
    figdir = join(wrkdir, "figs")
else:
    png = ".png"
    figdir = join(wrkdir, "pngs")
if not os.path.exists(figdir):
    os.mkdir(figdir)


os.chdir(simsdir)
iset = [1, 2, 3, 4, 5, 6, 7, 10, 11, 8, 9, 0, 12]
# iset = [1,2,3,4,5,6,7,10,11,8,9]
sims_list = list(pc.math.natural_sort(glob.glob("dung_gputest2")))
print(sims_list)
# for sim in sims_list:
#    if not pc.is_sim_dir(join(simsdir,sim)):
#        sims_list.remove(sim)
sims = np.array(sims_list)[0,]

iset = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
# print(sims[iset],len(sims), len(iset))
eta_0 = 1e-3
nu_0 = 1e-3

SNI_area_rate_cgs = 1.330982784e-56
ts_dict = {}
gd_dict = {}
par_dict = {}
pwr_dict = {}
mean_b_dict = {}
os.chdir(wrkdir)
tsteps = {}

# iset = [0,1,4,5]
for sim in [sims]:
    os.chdir(os.path.join(simsdir, sim))
    print(sim)
    ts = pc.read.ts()
    tstmin = ts.t.min()
    ts.t -= tstmin
    print("ts.t.min()", ts.t.min(), tstmin)
    if sim == "H2":
        tdelay = 40.0
    else:
        tdelay = 20.0
    try:
        av = pc.read.aver(
            plane_list="xy", var_names=avkeys, precision="f", time_range=None
        )
    except Exception:
        print(f"waiting {tdelay:.1f} seconds for averages to be available")
        time.sleep(tdelay)
        av = pc.read.aver(
            plane_list="xy", var_names=avkeys, precision="f", time_range=None
        )
    print("size av.t", av.t.size)
    ekinturb = (
        av.xy.ekinmz
        - 0.5 * (av.xy.ruxmz**2 + av.xy.ruymz**2 + av.xy.ruzmz**2) / av.xy.rhomz
    )
    ekinm = ekinturb.mean(axis=1)
    av.t -= tstmin
    interpt = interp1d(av.t, ekinm, axis=0, fill_value="extrapolate")
    tmp = interpt(ts.t)
    ts.__setattr__("eB", 0.5 * ts.brms**2 / tmp.mean())
    # tsteps[sim]=[ts.t[np.where(ts.brms==ts.brms.min())[0][0]],ts.t[np.where(ts.eB>0.05*ts.eB.max())[0][0]]]
    try:
        ts2 = ts.t[np.where(ts.eB < 0.06)[0][-1]]
    except Exception:
        ts2 = ts.t.max()
    ts0 = ts.t[np.where(ts.brms == ts.brms.min())[0][0]]
    if sim == "H2" or sim == "M2":
        ts1 = ts.t[np.where(ts.eB > 1e-6)[0][0]]
        ts2 = ts.t[np.where(ts.eB < 0.06)[0][-1]]
    else:
        ts1 = 0.06
    ts3 = 0.7
    ts_dict[sim] = ts
    tsteps[sim] = [ts0, ts1, ts2, ts3]
    gd_dict[sim] = pc.read.grid(trim=True)
    par = pc.read.param(append_units=True, conflicts_quiet=True)
    par.__setattr__(
        "SNI_area_rate",
        SNI_area_rate_cgs * par.unit_length**3 / par.unit_velocity * 1e-3 / par.lxyz[2],
    )
    par_dict[sim] = par
    pwr = pc.read.power()
    pwr.t -= tstmin
    print(sim, "pwr size ", pwr.t.size, "ssd start end", tsteps[sim])
    keys = list(pwr.__dict__.keys())
    for key in keys:
        if not key == "t" and not key == "krms":
            tmp = (
                gf(pwr.__getattribute__(key), sigma=[0.5, 1.0], mode="nearest")
                * par.unit_energy_density
            )
            if "kin" in key:
                tmp *= ts.rhom.mean()
            pwr.__setattr__(key + "_smoothed", tmp)
            tmp = (
                gf(pwr.__getattribute__(key), sigma=[2.5, 1.0], mode="nearest")
                * par.unit_energy_density
            )
            if "kin" in key:
                tmp *= ts.rhom.mean()
            pwr.__setattr__(key + "_25smoothed", tmp)
    pwr_dict[sim] = pwr

lst = []
lws = []
j = 0
for lsty, lw in zip(lstyle[:3], [1.0, 1.4, 1.8]):
    lws.append([lw, (4.0 - lw) / (3.0 + j)])
    for colr, lsty in zip(["magenta", "orange", "blue"], lstyle[:3]):
        lst.append([lsty, colr])
    j += 1.5
lws = np.array(lws)
lst = np.array(lst)

plt.figure(figsize=figsize)
nsamp = 50
nsampl = 6
istart = 70
for _isim in [
    0,
]:
    fig, ax = plt.subplots(
        1, 2, sharey=False, figsize=[figsize[0] * 1.7, figsize[1] * 0.9]
    )
    ilst = np.mod(np.array(iset), 3)
    for sim, lsty, lw, _mk in zip([sims], lst[ilst], lws[ilst], ["+", "<", "d"]):
        par = par_dict[sim]
        pwr = pwr_dict[sim]
        krms = pwr.krms[1:] / par.lxyz[0] * 2 * np.pi
        # it = np.where(pwr.t >= tsteps[sim][1])[0][0]
        it = 0
        label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.eta / eta_0:.1f}\eta_0$"
        ax[0].loglog(
            krms,
            pwr.mag_smoothed[it, 1:],
            ls=lsty[0],
            color=lsty[1],
            lw=lw[0],
            marker=None,
            markersize=3.5,
            fillstyle="none",
            alpha=lw[1],
            label=label,
        )
        label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0$"
        ax[1].loglog(
            krms,
            pwr.kin_smoothed[it, 1:],
            ls=lsty[0],
            color=lsty[1],
            lw=lw[0],
            marker=None,
            markersize=3.5,
            fillstyle="none",
            alpha=lw[1],
            label=label,
        )
    ax[0].set_ylabel(r"$P_B(k)$ [erg cm$^{-3}$]")
    ax[0].set_ylim([9e-22, 8e-16])
    ax[0].set_xlabel(r"$k$ [kpc$^{-1}$]")
    ax[0].tick_params(which="both", direction="in", top=True, right=True)
    ax[0].legend(framealpha=0.4, ncol=1)
    ax[1].set_ylabel(r"$P_K(k)$ [erg cm$^{-3}$]")
    ax[1].set_ylim([2e-17, 2e-12])
    ax[1].set_xlabel(r"$k$ [kpc$^{-1}$]")
    ax[1].tick_params(which="both", direction="in", top=True, right=True)
    ax[1].legend(framealpha=0.4, ncol=1)
    plt.tight_layout()
    if "eta" not in sim:
        plt.savefig(join(figdir, f"power-{sim[:2]}SSD" + png))
    else:
        plt.savefig(join(figdir, f"power-{sim[:2]}eta" + png))
    plt.close()
exit()
# for isim in [[0, 1, 2], [3, 4, 5], [6, 7, 8], [6, 9, 10]]:
#     fig, ax = plt.subplots(
#         1, 2, sharey=False, figsize=[figsize[0] * 1.7, figsize[1] * 0.9]
#     )
#     ilst = np.mod(0, 3)
#     for sim, lsty, lw, _mk in zip(sims[isim], lst[ilst], lws[ilst], ["+", "<", "d"]):
#         print(sim)
#         par = par_dict[sim]
#         pwr = pwr_dict[sim]
#         krms = pwr.krms[1:] / par.lxyz[0] * 2 * np.pi
#         try:
#             it = np.where(pwr.t >= tsteps[sim][2])[0][0]
#         except:
#             it = -1
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.eta / eta_0:.1f}\eta_0$"
#         ax[0].loglog(
#             krms,
#             pwr.mag_25smoothed[it, 1:],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0$"
#         ax[1].loglog(
#             krms,
#             pwr.kin_25smoothed[it, 1:],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#     ax[0].set_ylabel(r"$P_B(k)$ [erg cm$^{-3}$]")
#     ax[0].set_ylim([2e-19, 1e-15])
#     ax[0].set_xlabel(r"$k$ [kpc$^{-1}$]")
#     ax[0].tick_params(which="both", direction="in", top=True, right=True)
#     ax[0].legend(framealpha=0.4, ncol=1)
#     ax[1].set_ylabel(r"$P_K(k)$ [erg cm$^{-3}$]")
#     ax[1].set_ylim([2e-17, 2e-12])
#     ax[1].set_xlabel(r"$k$ [kpc$^{-1}$]")
#     ax[1].tick_params(which="both", direction="in", top=True, right=True)
#     ax[1].legend(framealpha=0.4, ncol=1)
#     plt.tight_layout()
#     if "eta" not in sim:
#         plt.savefig(join(figdir, f"power-{sim[:2]}trans" + png))
#     else:
#         plt.savefig(join(figdir, f"power-{sim[:2]}teta" + png))
#     plt.close()
#
# for isim in [[9, 0, 7], [10, 0, 8]]:
#     fig, ax = plt.subplots(
#         1, 2, sharey=False, figsize=[figsize[0] * 1.7, figsize[1] * 0.9]
#     )
#     ilst = np.mod(np.array(iset), 3)
#     for sim, lsty, lw, _mk in zip(sims[isim], lst[ilst], lws[ilst], ["+", "<", "d"]):
#         if not sim == sims[0]:
#             print(sim)
#             par = par_dict[sim]
#             pwr = pwr_dict[sim]
#             krms = pwr.krms[1:] / par.lxyz[0] * 2 * np.pi
#             try:
#                 it = np.where(pwr.t >= tsteps[sim][2])[0][0]
#             except:
#                 it = -1
#             label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.eta / eta_0:.1f}\eta_0$"
#             ax[0].loglog(
#                 krms,
#                 pwr.mag_25smoothed[it, 1:],
#                 ls=lsty[0],
#                 color=lsty[1],
#                 lw=lw[0],
#                 marker=None,
#                 markersize=3.5,
#                 fillstyle="none",
#                 alpha=lw[1],
#                 label=label,
#             )
#             label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0$"
#             ax[1].loglog(
#                 krms,
#                 pwr.kin_25smoothed[it, 1:],
#                 ls=lsty[0],
#                 color=lsty[1],
#                 lw=lw[0],
#                 marker=None,
#                 markersize=3.5,
#                 fillstyle="none",
#                 alpha=lw[1],
#                 label=label,
#             )
#     ax[0].set_ylabel(r"$P_B(k)$ [erg cm$^{-3}$]")
#     ax[0].set_ylim([2e-19, 1e-15])
#     ax[0].set_xlabel(r"$k$ [kpc$^{-1}$]")
#     ax[0].tick_params(which="both", direction="in", top=True, right=True)
#     ax[0].legend(framealpha=0.4, ncol=1)
#     ax[1].set_ylabel(r"$P_K(k)$ [erg cm$^{-3}$]")
#     ax[1].set_ylim([2e-17, 2e-12])
#     ax[1].set_xlabel(r"$k$ [kpc$^{-1}$]")
#     ax[1].tick_params(which="both", direction="in", top=True, right=True)
#     ax[1].legend(framealpha=0.4, ncol=1)
#     plt.tight_layout()
#     plt.savefig(join(figdir, f"power-{par.eta / eta_0:.1f}etapair" + png))
#     plt.close()
#
# for isim in [[0, 3, 6], [1, 4, 7], [2, 5, 8]]:
#     fig, ax = plt.subplots(
#         1, 2, sharey=False, figsize=[figsize[0] * 1.7, figsize[1] * 0.9]
#     )
#     ilst = np.mod(np.array(iset), 3)
#     for sim, lsty, lw, _mk in zip(sims[isim], lst[ilst], lws[ilst], ["+", "<", "d"]):
#         print(sim)
#         par = par_dict[sim]
#         pwr = pwr_dict[sim]
#         krms = pwr.krms[1:] / par.lxyz[0] * 2 * np.pi
#         try:
#             it = np.where(pwr.t >= tsteps[sim][2])[0][0]
#         except:
#             it = -1
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.eta / eta_0:.1f}\eta_0$"
#         ax[0].loglog(
#             krms,
#             pwr.mag_25smoothed[it, 1:],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0$"
#         ax[1].loglog(
#             krms,
#             pwr.kin_25smoothed[it, 1:],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#     ax[0].set_ylabel(r"$P_B(k)$ [erg cm$^{-3}$]")
#     ax[0].set_ylim([2e-19, 1e-15])
#     ax[0].set_xlabel(r"$k$ [kpc$^{-1}$]")
#     ax[0].tick_params(which="both", direction="in", top=True, right=True)
#     ax[0].legend(framealpha=0.4, ncol=1)
#     ax[1].set_ylabel(r"$P_K(k)$ [erg cm$^{-3}$]")
#     ax[1].set_ylim([2e-17, 2e-12])
#     ax[1].set_xlabel(r"$k$ [kpc$^{-1}$]")
#     ax[1].tick_params(which="both", direction="in", top=True, right=True)
#     ax[1].legend(framealpha=0.4, ncol=1)
#     plt.tight_layout()
#     if "eta" not in sim:
#         plt.savefig(join(figdir, f"power-{par.eta}trans" + png))
#     else:
#         plt.savefig(join(figdir, f"power-{par.eta}teta" + png))
#     plt.close()
#
# for isim in [
#     [0, 3, 6],
# ]:
#     fig, ax = plt.subplots(
#         1, 2, sharey=False, figsize=[figsize[0] * 1.7, figsize[1] * 0.9]
#     )
#     ilst = np.mod(np.array(iset), 3)
#     for sim, lsty, lw, _mk in zip(sims[isim], lst[ilst], lws[ilst], ["+", "<", "d"]):
#         print(sim)
#         par = par_dict[sim]
#         pwr = pwr_dict[sim]
#         krms = pwr.krms[1:] / par.lxyz[0] * 2 * np.pi
#         try:
#             it = np.where(pwr.t >= tsteps[sim][3])[0][0]
#         except:
#             it = -1
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.eta / eta_0:.1f}\eta_0$"
#         ax[0].loglog(
#             krms,
#             pwr.mag_25smoothed[it, 1:],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0$"
#         ax[1].loglog(
#             krms,
#             pwr.kin_25smoothed[it, 1:],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#     ax[0].set_ylabel(r"$P_B(k)$ [erg cm$^{-3}$]")
#     # ax[0].set_ylim([2e-19,1e-15])
#     ax[0].set_xlabel(r"$k$ [kpc$^{-1}$]")
#     ax[0].tick_params(which="both", direction="in", top=True, right=True)
#     ax[0].legend(framealpha=0.4, ncol=1)
#     ax[1].set_ylabel(r"$P_K(k)$ [erg cm$^{-3}$]")
#     ax[1].set_ylim([2e-17, 2e-12])
#     ax[1].set_xlabel(r"$k$ [kpc$^{-1}$]")
#     ax[1].tick_params(which="both", direction="in", top=True, right=True)
#     ax[1].legend(framealpha=0.4, ncol=1)
#     plt.tight_layout()
#     plt.savefig(join(figdir, f"power-{par.eta}fast" + png))
#     plt.close()
#
# for isim in [[12, 0, 11]]:
#     fig, ax = plt.subplots(
#         1, 2, sharey=False, figsize=[figsize[0] * 1.7, figsize[1] * 0.9]
#     )
#     ilst = np.mod(np.array(iset), 3)
#     for sim, lsty, lw, _mk in zip(sims[isim], lst[ilst], lws[ilst], ["+", "<", "d"]):
#         if not sim == sims[0]:
#             print(sim)
#             par = par_dict[sim]
#             pwr = pwr_dict[sim]
#             gd = gd_dict[sim]
#             krms = pwr.krms[1:] / par.lxyz[0] * 2 * np.pi
#             try:
#                 it = np.where(pwr.t >= tsteps[sim][2])[0][0]
#             except:
#                 it = -1
#             label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.eta / eta_0:.1f}\eta_0,\,{gd.dx * 1e3:.0f}pc$"
#             ax[0].loglog(
#                 krms,
#                 pwr.mag_25smoothed[it, 1:],
#                 ls=lsty[0],
#                 color=lsty[1],
#                 lw=lw[0],
#                 marker=None,
#                 markersize=3.5,
#                 fillstyle="none",
#                 alpha=lw[1],
#                 label=label,
#             )
#             label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0,\,{gd.dx * 1e3:.0f}pc$"
#             ax[1].loglog(
#                 krms,
#                 pwr.kin_25smoothed[it, 1:],
#                 ls=lsty[0],
#                 color=lsty[1],
#                 lw=lw[0],
#                 marker=None,
#                 markersize=3.5,
#                 fillstyle="none",
#                 alpha=lw[1],
#                 label=label,
#             )
#     ax[0].set_ylabel(r"$P_B(k)$ [erg cm$^{-3}$]")
#     ax[0].set_ylim([2e-19, 1e-15])
#     ax[0].set_xlabel(r"$k$ [kpc$^{-1}$]")
#     ax[0].tick_params(which="both", direction="in", top=True, right=True)
#     ax[0].legend(framealpha=0.4, ncol=1)
#     ax[1].set_ylabel(r"$P_K(k)$ [erg cm$^{-3}$]")
#     ax[1].set_ylim([2e-17, 2e-12])
#     ax[1].set_xlabel(r"$k$ [kpc$^{-1}$]")
#     ax[1].tick_params(which="both", direction="in", top=True, right=True)
#     ax[1].legend(framealpha=0.4, ncol=1)
#     plt.tight_layout()
#     if "eta" not in sim:
#         plt.savefig(join(figdir, f"power-{sim[:2]}trans" + png))
#     else:
#         plt.savefig(join(figdir, f"power-{sim[:2]}teta" + png))
#     plt.close()
#
# for isim in [[12, 0, 11]]:
#     fig, ax = plt.subplots(1, 1, sharex=True, figsize=figsize)
#     ilst = np.mod(np.array(iset), 3)
#     for sim, lsty, lw, _mk in zip(sims[isim], lst[ilst], lws[ilst], ["+", "<", "d"]):
#         if not sim == sims[0]:
#             print(sim)
#             par = par_dict[sim]
#             pwr = pwr_dict[sim]
#             gd = gd_dict[sim]
#             krms = pwr.krms[1:] / par.lxyz[0] * 2 * np.pi
#             if sim == "H2":
#                 tshift = tsteps["M2"][2] - tsteps["H2"][2]
#                 it = np.where(pwr.t >= tsteps[sim][1])[0][0]
#             else:
#                 tshift = 0
#                 it = np.where(pwr.t >= tsteps[sim][1])[0][0]
#             label = (
#                 rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0,\,{par.eta / eta_0:.1f}\eta_0,\,{gd.dx * 1e3:.0f}pc$"
#             )
#             ax.plot(
#                 pwr.t[it:] + tshift,
#                 pwr.mag[it:, :3].sum(axis=1) / pwr.mag[it:].sum(axis=1),
#                 ls=lsty[0],
#                 color=lsty[1],
#                 lw=lw[0],
#                 marker=None,
#                 markersize=3.5,
#                 fillstyle="none",
#                 alpha=lw[1],
#                 label=label,
#             )
#     ax.set_ylabel(r"$\Sigma_{k<5k_1}P_B/\Sigma_k P_B$")
#     ax.set_ylim([0.0, 1.0])
#     ax.tick_params(which="both", direction="in", top=True, right=True)
#     ax.legend(framealpha=0.4, ncol=1)
#     ax.set_xlabel(r"$t$ [Gyr]")
#     plt.tight_layout()
#     if "eta" not in sim:
#         plt.savefig(join(figdir, f"tpower-{sim[:2]}" + png))
#     else:
#         plt.savefig(join(figdir, f"tpower-{sim[:2]}" + png))
#     plt.close()
#
# for isim in [[12, 0, 11]]:
#     fig, ax = plt.subplots(1, 1, sharex=True, figsize=figsize)
#     ilst = np.mod(np.array(iset), 3)
#     for sim, lsty, lw, _mk in zip(sims[isim], lst[ilst], lws[ilst], ["+", "<", "d"]):
#         if not sim == sims[0]:
#             print(sim)
#             par = par_dict[sim]
#             pwr = pwr_dict[sim]
#             gd = gd_dict[sim]
#             krms = pwr.krms[1:] / par.lxyz[0] * 2 * np.pi
#             if sim == "H2":
#                 tshift = tsteps["M2"][2] - tsteps["H2"][2]
#                 it = np.where(pwr.t >= tsteps[sim][0])[0][0]
#             else:
#                 tshift = 0
#                 it = np.where(pwr.t >= tsteps[sim][0])[0][0]
#             label = (
#                 rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0,\,{par.eta / eta_0:.1f}\eta_0,\,{gd.dx * 1e3:.0f}pc$"
#             )
#             ax.plot(
#                 pwr.t[it:] + tshift,
#                 pwr.mag[it:, :3].sum(axis=1) / pwr.mag[it:].sum(axis=1),
#                 ls=lsty[0],
#                 color=lsty[1],
#                 lw=lw[0],
#                 marker=None,
#                 markersize=3.5,
#                 fillstyle="none",
#                 alpha=lw[1],
#                 label=label,
#             )
#     ax.set_ylabel(r"$\Sigma_{k<5k_1}P_B/\Sigma_k P_B$")
#     ax.set_ylim([0.0, 1.0])
#     ax.tick_params(which="both", direction="in", top=True, right=True)
#     ax.legend(framealpha=0.4, ncol=1)
#     ax.set_xlabel(r"$t$ [Gyr]")
#     plt.tight_layout()
#     if "eta" not in sim:
#         plt.savefig(join(figdir, f"tpower-{sim[:2]}x" + png))
#     else:
#         plt.savefig(join(figdir, f"tpower-{sim[:2]}" + png))
#     plt.close()
#
# for isim in [[6, 9, 10]]:
#     fig, ax = plt.subplots(1, 1, sharex=True, figsize=figsize)
#     ilst = np.mod(np.array(iset), 3)
#     for sim, lsty, lw, _mk in zip(sims[isim], lst[ilst], lws[ilst], ["+", "<", "d"]):
#         if not sim == sims[0]:
#             print(sim)
#             par = par_dict[sim]
#             pwr = pwr_dict[sim]
#             gd = gd_dict[sim]
#             krms = pwr.krms[1:] / par.lxyz[0] * 2 * np.pi
#             if sim == "H2":
#                 tshift = 0.95
#                 it = np.where(pwr.t >= tsteps[sim][0])[0][0]
#             else:
#                 tshift = 0
#                 it = np.where(pwr.t >= tsteps[sim][1])[0][0]
#             label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0,\,{par.eta / eta_0:.1f}\eta_0$"
#             ax.plot(
#                 pwr.t[it:] + tshift,
#                 pwr.mag[it:, :3].sum(axis=1) / pwr.mag[it:].sum(axis=1),
#                 ls=lsty[0],
#                 color=lsty[1],
#                 lw=lw[0],
#                 marker=None,
#                 markersize=3.5,
#                 fillstyle="none",
#                 alpha=lw[1],
#                 label=label,
#             )
#     ax.set_ylabel(r"$\Sigma_{k<5k_1}P_B/\Sigma_k P_B$")
#     ax.set_ylim([0.0, 1.0])
#     ax.tick_params(which="both", direction="in", top=True, right=True)
#     ax.legend(framealpha=0.4, ncol=1)
#     ax.set_xlabel(r"$t$ [Gyr]")
#     plt.tight_layout()
#     if "eta" not in sim:
#         plt.savefig(join(figdir, f"tpower-{sim[:2]}" + png))
#     else:
#         plt.savefig(join(figdir, f"tpower-{sim[:2]}" + png))
#     plt.close()
#
# fig, ax = plt.subplots(3, 1, sharex=True, figsize=[figsize[0], figsize[1] * 2.6])
# iplot = 0
# for isim in [[0, 3, 6], [1, 4, 7], [2, 5, 8]]:
#     ilst = np.mod(np.array(iset), 3)
#     for sim, lsty, lw, _mk in zip(sims[isim], lst[ilst], lws[ilst], ["+", "<", "d"]):
#         print(sim)
#         par = par_dict[sim]
#         pwr = pwr_dict[sim]
#         krms = pwr.krms[1:] / par.lxyz[0] * 2 * np.pi
#         if sim == "H2":
#             tshift = 0.95
#             it = np.where(pwr.t >= tsteps[sim][0])[0][0]
#         else:
#             tshift = 0
#             it = np.where(pwr.t >= tsteps[sim][1])[0][0]
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0,\,{par.eta / eta_0:.1f}\eta_0$"
#         ax[iplot].plot(
#             pwr.t[it:] + tshift,
#             pwr.mag[it:, :3].sum(axis=1) / pwr.mag[it:].sum(axis=1),
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#     ax[iplot].set_ylabel(r"$\Sigma_{k<5k_1}P_B/\Sigma_k P_B$")
#     ax[iplot].set_ylim([0.0, 1.0])
#     ax[iplot].tick_params(which="both", direction="in", top=True, right=True)
#     ax[iplot].legend(framealpha=0.4, ncol=1)
#     iplot += 1
#     # ax[1].set_ylim([2e-17,2e-12])
# ax[2].set_xlabel(r"$t$ [Gyr]")
# plt.tight_layout()
# plt.savefig(join(figdir, "tpower-all" + png))
# plt.close()
#
# for isim in [[7, 9], [8, 10]]:
#     fig, ax = plt.subplots(
#         1, 2, sharey=False, figsize=[figsize[0] * 1.7, figsize[1] * 0.9]
#     )
#     ilst = np.mod(np.array(iset), 3)
#     for sim, lsty, lw, _mk in zip(sims[isim], lst[ilst], lws[ilst], ["+", "<", "d"]):
#         print(sim)
#         par = par_dict[sim]
#         pwr = pwr_dict[sim]
#         krms = pwr.krms[1:] / par.lxyz[0] * 2 * np.pi
#         try:
#             it = np.where(pwr.t >= tsteps[sim][1])[0][0]
#         except:
#             it = -1
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.eta / eta_0:.1f}\eta_0$"
#         ax[0].loglog(
#             krms,
#             pwr.mag_smoothed[it, 1:],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0$"
#         ax[1].loglog(
#             krms,
#             pwr.kin_smoothed[it, 1:],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#     ax[0].set_ylabel(r"$P_B(k)$ [erg cm$^{-3}$]")
#     ax[0].set_ylim([2e-19, 1e-15])
#     ax[0].tick_params(which="both", direction="in", top=True, right=True)
#     ax[0].legend(framealpha=0.4, ncol=1)
#     ax[1].set_ylabel(r"$P_K(k)$ [erg cm$^{-3}$]")
#     ax[1].set_ylim([2e-17, 2e-12])
#     ax[1].set_xlabel(r"$k$ [kpc$^{-1}$]")
#     ax[1].tick_params(which="both", direction="in", top=True, right=True)
#     ax[1].legend(framealpha=0.4, ncol=1)
#     plt.tight_layout()
#     plt.savefig(
#         join(figdir, f"power-{sim[:2]}teta{par.eta / eta_0:.1f}" + png)
#     )
#     plt.close()
#
# eta_0 = 1e-3
# nu_0 = 1e-3
# xlim = [-0.005, 1.85]
# ylim = [3e-4, 10.0]
#
# lst = []
# lws = []
# j = 0
# for colr in ["magenta", "orange", "blue"]:
#     for lsty, lw in zip(lstyle[:3], [1.0, 1.4, 1.8]):
#         lst.append([lsty, colr])
#         lws.append([lw, (4.0 - lw) / (3.0 + j)])
#     j += 1.5
# lws = np.array(lws)
# lst = np.array(lst)
#
# plt.figure(figsize=figsize)
# j = 0
# for isim in [[12, 11]]:
#     for sim, lsty, lw, _mk in zip(
#         sims[isim], lst[[6 + j, 5 + j]], lws[[0, 4]], ["+", "<"]
#     ):
#         ts = ts_dict[sim]
#         par = par_dict[sim]
#         gd = gd_dict[sim]
#         if sim == "H2":
#             tshift = tstart
#         else:
#             tshift = 0.0
#             tstart = tsteps["M2"][2] - tsteps["H2"][2]
#         print("sim, dx", sim, gd.dx)
#         skip = 1  # max(int(ts.t.size/40),1)
#         label = (
#             rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0,\,{par.eta / eta_0:.1f}\eta_0,\,{gd.dx * 1e3:.0f}$ pc"
#         )
#         plt.semilogy(
#             ts.t[::skip] + tshift,
#             ts.eB[::skip],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#     j -= 3
# plt.legend(fontsize=0.85 * fontsize, framealpha=0.5, ncol=1)
# plt.tick_params(which="both", direction="in", top=True, right=True)
# plt.xlabel(r"$t$ [Gyr]")
# plt.ylim([2e-11, 9])
# plt.ylabel(r"$e_B/\overline{e_K^\prime}$")
# plt.tight_layout()
# plt.savefig(figdir + "L2res" + png)
# plt.close()
#
# for isim in [[0, 1, 2], [3, 4, 5], [6, 7, 8]]:
#     plt.figure(figsize=figsize)
#     for sim, lsty, lw, _mk in zip(sims[isim], lst[isim], lws[isim], ["+", "<", "d"]):
#         ts = ts_dict[sim]
#         par = par_dict[sim]
#         skip = 1  # max(int(ts.t.size/40),1)
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0,\,{par.eta / eta_0:.1f}\eta_0$"
#         plt.semilogy(
#             ts.t[::skip],
#             ts.eB[::skip],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#     plt.legend(fontsize=0.85 * fontsize, framealpha=0.5, ncol=1)
#     plt.tick_params(which="both", direction="in", top=True, right=True)
#     plt.xlabel(r"$t$ [Gyr]")
#     plt.xlim(xlim)
#     plt.ylim(ylim)
#     plt.ylabel(r"$e_B/\overline{e_K^\prime}$")
#     plt.tight_layout()
#     plt.savefig(figdir + f"eBt{sim[:2]}all" + png)
#     plt.close()
#
# for isim in [[0, 3, 6], [1, 4, 7], [2, 5, 8]]:
#     plt.figure(figsize=figsize)
#     for sim, lsty, lw, _mk in zip(
#         sims[isim], lst[isim], lws[[0, 1, 2]], ["+", "<", "d"]
#     ):
#         ts = ts_dict[sim]
#         par = par_dict[sim]
#         skip = 1  # max(int(ts.t.size/40),1)
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0,\,{par.eta / eta_0:.1f}\eta_0$"
#         plt.semilogy(
#             ts.t[::skip],
#             ts.eB[::skip],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#     plt.legend(fontsize=0.85 * fontsize, framealpha=0.5, ncol=1)
#     plt.tick_params(which="both", direction="in", top=True, right=True)
#     plt.xlabel(r"$t$ [Gyr]")
#     plt.xlim(xlim)
#     plt.ylim(ylim)
#     plt.ylabel(r"$e_B/\overline{e_K^\prime}$")
#     plt.tight_layout()
#     plt.savefig(figdir + f"eBt{sim[4:]}all" + png)
#     plt.close()
#
# for isim in [[6, 9, 10]]:
#     plt.figure(figsize=figsize)
#     for sim, lsty, lw, _mk in zip(
#         sims[isim], lst[[6, 4, 2]], lws[[0, 4, 8]], ["+", "<", "d"]
#     ):
#         ts = ts_dict[sim]
#         par = par_dict[sim]
#         print("sim, nu, eta", sim, par.nu, par.eta)
#         skip = 1  # max(int(ts.t.size/40),1)
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0,\,{par.eta / eta_0:.1f}\eta_0$"
#         plt.semilogy(
#             ts.t[::skip],
#             ts.eB[::skip],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#     plt.legend(fontsize=0.85 * fontsize, framealpha=0.5, ncol=1)
#     plt.tick_params(which="both", direction="in", top=True, right=True)
#     plt.xlabel(r"$t$ [Gyr]")
#     plt.xlim(xlim)
#     plt.ylim(ylim)
#     plt.ylabel(r"$e_B/\overline{e_K^\prime}$")
#     plt.tight_layout()
#     plt.savefig(figdir + "L4eta" + png)
#     plt.close()
#
# plt.figure(figsize=figsize)
# j = 0
# for isim in [[9, 7], [10, 8]]:
#     for sim, lsty, lw, _mk in zip(
#         sims[isim], lst[[6 + j, 6 + j]], lws[[0, 4]], ["+", "<"]
#     ):
#         ts = ts_dict[sim]
#         par = par_dict[sim]
#         print("sim, nu, eta", sim, par.nu, par.eta)
#         skip = 1  # max(int(ts.t.size/40),1)
#         label = rf"${sim[1]}\Omega_{{\rm Sn}},\,{par.nu / nu_0:.0f}\nu_0,\,{par.eta / eta_0:.1f}\eta_0$"
#         plt.semilogy(
#             ts.t[::skip],
#             ts.eB[::skip],
#             ls=lsty[0],
#             color=lsty[1],
#             lw=lw[0],
#             marker=None,
#             markersize=3.5,
#             fillstyle="none",
#             alpha=lw[1],
#             label=label,
#         )
#     j -= 3
# plt.legend(fontsize=0.85 * fontsize, framealpha=0.5, ncol=1)
# plt.tick_params(which="both", direction="in", top=True, right=True)
# plt.xlabel(r"$t$ [Gyr]")
# plt.xlim(xlim)
# plt.ylim(ylim)
# plt.ylabel(r"$e_B/\overline{e_K^\prime}$")
# plt.tight_layout()
# plt.savefig(figdir + "L4etapair" + png)
# plt.close()
